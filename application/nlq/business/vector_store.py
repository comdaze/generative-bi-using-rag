import boto3
import json
import requests
from nlq.data_access.opensearch import OpenSearchDao
from utils.env_var import BEDROCK_REGION, AOS_HOST, AOS_PORT, AOS_USER, AOS_PASSWORD, opensearch_info, embedding_info
from utils.env_var import bedrock_ak_sk_info
from utils.llm import invoke_model_sagemaker_endpoint
from utils.logging import getLogger

logger = getLogger()


class VectorStore:
    opensearch_dao = OpenSearchDao(AOS_HOST, AOS_PORT, AOS_USER, AOS_PASSWORD)
    # 不再在类初始化时创建 bedrock_client
    # 而是在需要时通过 get_bedrock_client() 获取

    @classmethod
    def get_all_samples(cls, profile_name):
        logger.info(f'get all samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_samples(opensearch_info['sql_index'], profile_name)

        sample_list = []
        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'text': sample['_source']['text'],
                'sql': sample['_source']['sql']
            })

        return sample_list

    @classmethod
    def get_all_entity_samples(cls, profile_name):
        logger.info(f'get all samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_entity_samples(opensearch_info['ner_index'], profile_name)

        sample_list = []
        if samples is None:
            return sample_list

        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'entity': sample['_source']['entity'],
                'comment': sample['_source']['comment'],
                'entity_type': sample['_source']['entity_type'],
                'entity_table_info': sample['_source']['entity_table_info']
            })

        return sample_list

    @classmethod
    def get_all_agent_cot_samples(cls, profile_name):
        logger.info(f'get all agent cot samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_agent_cot_samples(opensearch_info['agent_index'], profile_name)

        sample_list = []
        if samples is None:
            return sample_list

        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'query': sample['_source']['query'],
                'comment': sample['_source']['comment']
            })

        return sample_list

    @classmethod
    def add_sample(cls, profile_name, question, answer):
        logger.info(f'add sample question: {question} to profile {profile_name}')
        embedding = cls.create_vector_embedding(question)
        has_same_sample = cls.search_same_query(profile_name, 1, opensearch_info['sql_index'], embedding)
        if has_same_sample:
            logger.info(f'delete sample sample entity: {question} to profile {profile_name}')
        if cls.opensearch_dao.add_sample(opensearch_info['sql_index'], profile_name, question, answer, embedding):
            logger.info('Sample added')

    @classmethod
    def add_entity_sample(cls, profile_name, entity, comment, entity_type="metrics"):
        logger.info(f'add sample entity: {entity} to profile {profile_name}')
        embedding = cls.create_vector_embedding(entity)
        has_same_sample = cls.search_same_query(profile_name, 5, opensearch_info['ner_index'], embedding)
        if has_same_sample:
            logger.info(f'delete sample sample entity: {entity} to profile {profile_name}')
        if cls.opensearch_dao.add_entity_sample(opensearch_info['ner_index'], profile_name, entity, comment, embedding,
                                                entity_type):
            logger.info('Sample added')

    @classmethod
    def add_entity_dimension_batch_sample(cls, profile_name, entity, comment, entity_type="dimension", entity_info=[]):
        entity_value_set = set()
        for entity_table in entity_info:
            entity_value_set.add(
                entity_table["table_name"] + "#" + entity_table["column_name"] + "#" + entity_table["value"])
        logger.info(f'add sample entity: {entity} to profile {profile_name}')
        embedding = cls.create_vector_embedding(entity)
        same_dimension_value = cls.search_same_dimension_entity(profile_name, 5, opensearch_info['ner_index'],
                                                                embedding)
        if len(same_dimension_value) > 0:
            for dimension_value in same_dimension_value:
                entity_special_id = dimension_value["table_name"] + "#" + dimension_value["column_name"] + "#" + \
                                    dimension_value["value"]
                if entity_special_id not in entity_value_set:
                    entity_info.append(dimension_value)
        logger.info("entity_table_info: " + str(entity_info))
        if cls.opensearch_dao.add_entity_sample(opensearch_info['ner_index'], profile_name, entity, comment, embedding,
                                                entity_type, entity_info):
            logger.info('Sample added')

    @classmethod
    def add_agent_cot_sample(cls, profile_name, entity, comment):
        logger.info(f'add agent sample query: {entity} to profile {profile_name}')
        embedding = cls.create_vector_embedding(entity)
        has_same_sample = cls.search_same_query(profile_name, 1, opensearch_info['agent_index'], embedding)
        if has_same_sample:
            logger.info(f'delete agent sample sample query: {entity} to profile {profile_name}')
        if cls.opensearch_dao.add_agent_cot_sample(opensearch_info['agent_index'], profile_name, entity, comment,
                                                   embedding):
            logger.info('Sample added')

    @classmethod
    def create_vector_embedding(cls, text):
        model_name = embedding_info["embedding_name"]
        if embedding_info["embedding_platform"] == "bedrock":
            return cls.create_vector_embedding_with_bedrock(text, model_name)
        elif embedding_info["embedding_platform"] == "brclient-api":
            return cls.create_vector_embedding_with_br_client_api(text, model_name)
        else:
            return cls.create_vector_embedding_with_sagemaker(text, model_name)


    @classmethod
    def create_vector_embedding_with_br_client_api(cls, text, model_name):
        try:
            api_url = embedding_info["br_client_url"]
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + embedding_info["br_client_key"]
            }
            
            # 根据模型名称选择合适的请求格式
            if "titan" in model_name.lower():
                body = {
                    "model": model_name,
                    "input": text,
                    "encoding_format": "float"
                }
            else:
                body = {
                    "model": model_name,
                    "input": text
                }
                
            logger.info(f"Calling BR Client API with body: {json.dumps(body)}")
            response = requests.post(api_url, headers=headers, data=json.dumps(body))
            response.raise_for_status()  # 确保请求成功
            
            response_info = response.json()
            logger.info(f"BR Client API response: {json.dumps(response_info)}")
            
            # 尝试从不同的响应格式中提取嵌入向量
            embedding = None
            
            # 检查常见的响应格式
            if 'embedding' in response_info:
                embedding = response_info['embedding']
            elif 'embeddings' in response_info:
                embedding = response_info['embeddings']
            elif 'data' in response_info:
                if isinstance(response_info['data'], list) and len(response_info['data']) > 0:
                    data_item = response_info['data'][0]
                    if isinstance(data_item, dict):
                        if 'embedding' in data_item:
                            embedding = data_item['embedding']
                        elif 'embeddings' in data_item:
                            embedding = data_item['embeddings']
                    else:
                        embedding = data_item
                else:
                    embedding = response_info['data']
            
            # 确保embedding是一个列表
            if embedding is None:
                logger.error(f"Could not find embedding in response: {response_info}")
                # 返回默认向量
                return [0.0] * int(embedding_info.get("embedding_dimension", 1536))
            
            # 如果embedding是嵌套列表，取第一个元素
            if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
                embedding = embedding[0]
            
            # 确保embedding是一个列表而不是字符串或其他类型
            if not isinstance(embedding, list):
                logger.error(f"Embedding is not a list: {type(embedding)}")
                # 返回默认向量
                return [0.0] * int(embedding_info.get("embedding_dimension", 1536))
            
            logger.info(f"Successfully extracted embedding, dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f'create_vector_embedding_with_br_client_api error: {str(e)}')
            # 返回一个默认的空向量
            return [0.0] * int(embedding_info.get("embedding_dimension", 1536))

    @classmethod
    def create_vector_embedding_with_bedrock(cls, text, model_name):
        try:
            # 导入 get_bedrock_client 函数
            from utils.llm import get_bedrock_client
            
            # 获取 Bedrock 客户端，使用默认区域
            bedrock = get_bedrock_client()
            
            # 根据模型名称确定请求体格式
            model_id = model_name.lower()
            if "titan" in model_id:
                payload = {"inputText": text}
            elif "cohere" in model_id:
                payload = {
                    "texts": [text],
                    "input_type": "search_document"
                }
            else:
                # 默认格式
                payload = {"inputText": text}
            
            body = json.dumps(payload)
            accept = "application/json"
            contentType = "application/json"
            
            # 添加日志
            logger.info(f"Calling Bedrock embedding model: {model_name}")
            
            try:
                response = bedrock.invoke_model(
                    body=body, modelId=model_name, accept=accept, contentType=contentType
                )
                response_body = json.loads(response.get("body").read())
                
                # 根据模型类型提取嵌入向量
                embedding = None
                if "titan" in model_id:
                    embedding = response_body.get("embedding")
                elif "cohere" in model_id:
                    embeddings = response_body.get("embeddings")
                    if embeddings and len(embeddings) > 0:
                        embedding = embeddings[0]
                
                # 如果没有找到嵌入向量，尝试其他常见字段
                if embedding is None:
                    if 'embedding' in response_body:
                        embedding = response_body['embedding']
                    elif 'embeddings' in response_body and isinstance(response_body['embeddings'], list):
                        embedding = response_body['embeddings'][0]
                
                if embedding is None:
                    logger.error(f"Could not find embedding in response: {response_body}")
                    # 返回默认向量
                    return [0.0] * int(embedding_info.get("embedding_dimension", 1536))
                
                return embedding
                
            except Exception as e:
                logger.error(f"Error calling Bedrock embedding model: {str(e)}")
                # 如果调用失败，返回默认向量
                return [0.0] * int(embedding_info.get("embedding_dimension", 1536))
                
        except Exception as e:
            logger.error(f"Error in create_vector_embedding_with_bedrock: {str(e)}")
            # 返回一个默认的空向量
            return [0.0] * int(embedding_info.get("embedding_dimension", 1536))

    @classmethod
    def create_vector_embedding_with_sagemaker(cls, text, model_name):
        try:
            # 根据AmazonQ.md中的分析，使用正确的请求格式
            body = json.dumps(
                {
                    "input": text
                }
            )
            logger.info(f"Calling embedding endpoint {model_name} with body: {body}")
            response = invoke_model_sagemaker_endpoint(model_name, body, model_type="embedding")
            
            # 处理响应 - 根据测试结果分析
            if isinstance(response, dict) and 'data' in response:
                # 处理嵌套结构 - EMD-Model-bge-m3-endpoint返回格式
                data = response.get('data', [])
                if isinstance(data, list) and len(data) > 0:
                    embedding_data = data[0]
                    if isinstance(embedding_data, dict) and 'embedding' in embedding_data:
                        embeddings = embedding_data['embedding']
                        logger.info(f"Successfully extracted embedding from data[0]['embedding'], dimension: {len(embeddings)}")
                        return embeddings
            
            # 如果上面的格式不匹配，尝试其他可能的格式
            if isinstance(response, dict) and 'embedding' in response:
                embeddings = response['embedding']
                return embeddings
            elif isinstance(response, list):
                embeddings = response[0] if len(response) > 0 else []
                return embeddings
            
            # 如果无法识别格式，记录错误并尝试备用方法
            logger.error(f"Unrecognized response format: {response}")
            
            # 尝试使用另一种格式重试
            try:
                logger.info("Retrying with alternative format (inputs array)")
                body = json.dumps(
                    {
                        "inputs": [text]
                    }
                )
                logger.info(f"Retrying embedding endpoint {model_name} with body: {body}")
                response = invoke_model_sagemaker_endpoint(model_name, body, model_type="embedding")
                
                if isinstance(response, list):
                    embeddings = response[0]
                else:
                    embeddings = response
                    
                return embeddings
            except Exception as retry_error:
                logger.error(f"Retry also failed: {str(retry_error)}")
                # 返回一个默认的空向量
                return [0.0] * int(embedding_info.get("embedding_dimension", 1536))
                
        except Exception as e:
            logger.error(f'create_vector_embedding_with_sagemaker is error {e}')
            # 返回一个默认的空向量
            return [0.0] * int(embedding_info.get("embedding_dimension", 1536))

    @classmethod
    def delete_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample(opensearch_info['sql_index'], profile_name, doc_id)
        print(ret)

    @classmethod
    def delete_entity_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample(opensearch_info['ner_index'], profile_name, doc_id)
        print(ret)

    @classmethod
    def delete_agent_cot_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample(opensearch_info['agent_index'], profile_name, doc_id)
        print(ret)

    @classmethod
    def search_sample(cls, profile_name, top_k, index_name, query):
        logger.info(f'search sample question: {query}  {index_name} from profile {profile_name}')
        sample_list = cls.opensearch_dao.search_sample(profile_name, top_k, index_name, query)
        return sample_list

    @classmethod
    def search_sample_with_embedding(cls, profile_name, top_k, index_name, query_embedding):
        sample_list = cls.opensearch_dao.search_sample_with_embedding(profile_name, top_k, index_name, query_embedding)
        return sample_list

    @classmethod
    def search_same_query(cls, profile_name, top_k, index_name, embedding):
        search_res = cls.search_sample_with_embedding(profile_name, top_k, index_name, embedding)
        if len(search_res) > 0:
            similarity_sample = search_res[0]
            similarity_score = similarity_sample["_score"]
            similarity_id = similarity_sample['_id']
            if similarity_score == 1.0:
                if index_name == opensearch_info['sql_index']:
                    cls.delete_sample(profile_name, similarity_id)
                    return True
                elif index_name == opensearch_info['ner_index']:
                    cls.delete_entity_sample(profile_name, similarity_id)
                    return True
                elif index_name == opensearch_info['agent_index']:
                    cls.delete_agent_cot_sample(profile_name, similarity_id)
                    return True
                else:
                    return False
        return False

    @classmethod
    def search_same_dimension_entity(cls, profile_name, top_k, index_name, embedding):
        search_res = cls.search_sample_with_embedding(profile_name, top_k, index_name, embedding)
        same_dimension_value = []
        if len(search_res) > 0:
            for i in range(len(search_res)):
                similarity_sample = search_res[i]
                similarity_score = similarity_sample["_score"]
                if similarity_score == 1.0:
                    if similarity_sample["_source"]["entity_type"] == "dimension":
                        entity_table_info = similarity_sample["_source"]["entity_table_info"]
                        for each in entity_table_info:
                            same_dimension_value.append(each)
                    sample_id = similarity_sample['_id']
                    VectorStore.delete_entity_sample(profile_name, sample_id)
        return same_dimension_value

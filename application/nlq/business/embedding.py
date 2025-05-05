import uuid
from nlq.data_access.dynamo_embedding import EmbeddingModelDao, EmbeddingModelEntity, GlobalSettingsDao, GlobalSettingEntity
from utils.logging import getLogger
import json
import boto3
from botocore.config import Config
import requests
from utils.env_var import embedding_info
from utils.env_var import bedrock_ak_sk_info

logger = getLogger()


class EmbeddingModelManagement:
    embedding_model_dao = EmbeddingModelDao()
    global_settings_dao = GlobalSettingsDao()

    @classmethod
    def get_all_embedding_models(cls):
        """获取所有嵌入模型"""
        logger.info('Getting all embedding models...')
        return [model.model_id for model in cls.embedding_model_dao.get_model_list()]

    @classmethod
    def get_all_embedding_models_with_info(cls):
        """获取所有嵌入模型及其详细信息"""
        logger.info('Getting all embedding models with info...')
        model_list = cls.embedding_model_dao.get_model_list()
        model_map = {}
        for model in model_list:
            model_map[model.model_id] = {
                'name': model.name,
                'platform': model.platform,
                'model_name': model.model_name,
                'region': model.region,
                'dimension': model.dimension,
                'api_url': model.api_url,
                'api_key': model.api_key,
                'input_format': model.input_format
            }
        return model_map

    @classmethod
    def get_embedding_model_by_id(cls, model_id):
        """根据ID获取嵌入模型"""
        return cls.embedding_model_dao.get_by_id(model_id)

    @classmethod
    def add_embedding_model(cls, name, platform, model_name, region=None, dimension=1536, api_url=None, api_key=None, input_format=None):
        """添加嵌入模型"""
        model_id = f"{platform}.{name}"
        entity = EmbeddingModelEntity(
            model_id=model_id,
            name=name,
            platform=platform,
            model_name=model_name,
            region=region or "",
            dimension=dimension,
            api_url=api_url or "",
            api_key=api_key or "",
            input_format=input_format or ""
        )
        cls.embedding_model_dao.add(entity)
        logger.info(f"Embedding model {model_id} added")
        return model_id

    @classmethod
    def update_embedding_model(cls, model_id, name=None, platform=None, model_name=None, region=None, dimension=None, api_url=None, api_key=None, input_format=None):
        """更新嵌入模型"""
        model = cls.embedding_model_dao.get_by_id(model_id)
        if not model:
            logger.error(f"Embedding model {model_id} not found")
            return False
        
        entity = EmbeddingModelEntity(
            model_id=model_id,
            name=name or model.name,
            platform=platform or model.platform,
            model_name=model_name or model.model_name,
            region=region if region is not None else model.region,
            dimension=dimension if dimension is not None else model.dimension,
            api_url=api_url if api_url is not None else model.api_url,
            api_key=api_key if api_key is not None else model.api_key,
            input_format=input_format if input_format is not None else model.input_format
        )
        cls.embedding_model_dao.update(entity)
        logger.info(f"Embedding model {model_id} updated")
        return True

    @classmethod
    def delete_embedding_model(cls, model_id):
        """删除嵌入模型"""
        # 检查是否为默认模型
        default_model = cls.get_global_setting('default_embedding_model')
        if default_model and default_model.setting_value == model_id:
            logger.error(f"Cannot delete model {model_id} as it is set as default")
            return False, "Cannot delete model as it is set as default"
        
        cls.embedding_model_dao.delete(model_id)
        logger.info(f"Embedding model {model_id} deleted")
        return True, f"Model {model_id} deleted successfully"

    @classmethod
    def test_embedding_model(cls, model_id, text, user_credentials=None):
        """测试嵌入模型"""
        model = cls.embedding_model_dao.get_by_id(model_id)
        if not model:
            return False, "Model not found"
        
        # 如果提供了用户凭证，将其添加到模型对象中
        original_input_format = model.input_format
        if user_credentials:
            logger.info("Using provided user credentials for testing")
            model.input_format = json.dumps({
                "credentials": user_credentials
            })
            logger.info(f"Temporary input_format set with credentials")
        
        try:
            if model.platform == "bedrock":
                return cls._test_bedrock_embedding(model, text)
            elif model.platform == "sagemaker":
                return cls._test_sagemaker_embedding(model, text)
            elif model.platform == "brclient-api":
                return cls._test_brclient_api_embedding(model, text)
            else:
                return False, f"Unsupported platform: {model.platform}"
        except Exception as e:
            logger.error(f"Error testing embedding model: {str(e)}")
            return False, f"Error: {str(e)}"
        finally:
            # 恢复原始的input_format
            if user_credentials:
                model.input_format = original_input_format

    @classmethod
    def _test_bedrock_embedding(cls, model, text):
        """测试Bedrock嵌入模型"""
        try:
            # 导入 get_bedrock_client 函数
            from utils.llm import get_bedrock_client
            
            # 检查模型中是否包含用户提供的凭证
            user_credentials = None
            logger.info(f"Model input_format: {model.input_format}")  # 添加日志
            
            if model.input_format:
                try:
                    input_data = json.loads(model.input_format)
                    logger.info(f"Parsed input_format: {json.dumps(input_data)}")  # 添加日志
                    if "credentials" in input_data:
                        user_credentials = input_data["credentials"]
                        logger.info("Found user credentials in input_format")  # 添加日志
                        # 不要记录实际凭证，但可以记录是否存在
                        logger.info(f"Has access_key_id: {'access_key_id' in user_credentials}")
                        logger.info(f"Has secret_access_key: {'secret_access_key' in user_credentials}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse input_format as JSON: {str(e)}")
            
            # 创建 Bedrock 客户端，使用模型的区域和可能的用户凭证
            bedrock = get_bedrock_client(region=model.region, user_credentials=user_credentials)
            
            # 根据模型名称确定请求体格式
            model_id = model.model_name.lower()
            if "titan" in model_id:
                body = json.dumps({
                    "inputText": text
                })
            elif "cohere" in model_id:
                body = json.dumps({
                    "texts": [text],
                    "input_type": "search_document"
                })
            else:
                # 默认格式
                body = json.dumps({
                    "inputText": text
                })
            
            # 添加请求日志
            logger.info(f"Calling Bedrock API with model: {model.model_name}")
            logger.info(f"Request body: {body}")
            
            # 调用Bedrock API
            response = bedrock.invoke_model(
                body=body,
                modelId=model.model_name
            )
            
            # 解析响应
            response_body = json.loads(response.get('body').read())
            
            # 根据模型类型提取嵌入向量
            embedding = None
            if "titan" in model_id:
                embedding = response_body.get('embedding')
            elif "cohere" in model_id:
                embeddings = response_body.get('embeddings')
                if embeddings and len(embeddings) > 0:
                    embedding = embeddings[0]
            
            # 如果没有找到嵌入向量，尝试其他常见字段
            if embedding is None:
                if 'embedding' in response_body:
                    embedding = response_body['embedding']
                elif 'embeddings' in response_body and isinstance(response_body['embeddings'], list):
                    embedding = response_body['embeddings'][0]
            
            if embedding is None:
                return False, f"Could not find embedding in response: {response_body}"
            
            # 返回结果
            return True, {
                "embedding": embedding[:5] + ["..."] + embedding[-5:] if len(embedding) > 10 else embedding,  # 只显示前5个和后5个元素
                "dimension": len(embedding),
                "model": model.name,
                "raw_response": response_body  # 添加原始响应以便调试
            }
        except Exception as e:
            logger.error(f"Error testing Bedrock embedding: {str(e)}")
            return False, f"Error: {str(e)}"

    @classmethod
    def _test_sagemaker_embedding(cls, model, text):
        """测试SageMaker嵌入模型"""
        try:
            sagemaker_client = boto3.client(service_name='sagemaker-runtime', region_name=model.region)
            
            # 构建请求体
            if model.input_format:
                try:
                    # 使用用户提供的输入格式
                    input_format = json.loads(model.input_format)
                    payload = {}
                    for key, value in input_format.items():
                        if value == "INPUT_TEXT":
                            payload[key] = text
                        else:
                            payload[key] = value
                except Exception as e:
                    logger.error(f"Error parsing input format: {str(e)}")
                    payload = {"input": text}  # 默认使用input作为键
            else:
                payload = {"input": text}  # 默认使用input作为键
            
            logger.info(f"SageMaker payload: {payload}")
            
            # 调用SageMaker端点
            response = sagemaker_client.invoke_endpoint(
                EndpointName=model.model_name,
                Body=json.dumps(payload),
                ContentType="application/json"
            )
            
            # 解析响应
            response_body = json.loads(response.get('Body').read())
            logger.info(f"SageMaker response: {response_body}")
            
            # 尝试不同的可能的响应格式
            embedding = None
            
            # 检查是否有data字段，这是vLLM格式的常见字段
            if 'data' in response_body and isinstance(response_body['data'], list):
                # vLLM格式通常是data列表中的第一个元素包含embedding
                data_item = response_body['data'][0]
                if 'embedding' in data_item:
                    embedding = data_item['embedding']
                    logger.info(f"Found embedding in data[0].embedding with length {len(embedding)}")
            
            # 如果上面没找到，尝试其他常见格式
            if embedding is None:
                if 'embedding' in response_body:
                    embedding = response_body['embedding']
                    logger.info(f"Found embedding in root.embedding with length {len(embedding)}")
                elif 'embeddings' in response_body:
                    embedding = response_body['embeddings']
                    logger.info(f"Found embedding in root.embeddings with length {len(embedding)}")
                elif isinstance(response_body, list):
                    embedding = response_body
                    logger.info(f"Response is a list, using as embedding with length {len(embedding)}")
            
            # 确保embedding是一个列表
            if embedding is None:
                embedding = []
                logger.error(f"Could not find embedding in response: {response_body}")
            
            # 如果embedding是嵌套列表，取第一个元素
            if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
                embedding = embedding[0]  # 有些模型返回嵌套列表
                logger.info(f"Extracted first element from nested list, length: {len(embedding)}")
            
            # 确保我们有足够的元素来显示
            dimension = len(embedding)
            logger.info(f"Final embedding dimension: {dimension}")
            
            # 准备样本数据
            if dimension > 0:
                first_five = embedding[:5] if dimension >= 5 else embedding
                last_five = embedding[-5:] if dimension >= 5 else []
                
                # 只有当embedding长度大于10时才添加省略号
                sample = first_five
                if dimension > 10:
                    sample = first_five + ["..."] + last_five
                elif dimension > 5:
                    sample = embedding  # 如果长度在5-10之间，显示全部
            else:
                sample = []
            
            # 返回结果
            return True, {
                "embedding": sample,
                "dimension": dimension,
                "model": model.name,
                "raw_response": response_body  # 添加原始响应以便调试
            }
        except Exception as e:
            logger.error(f"Error testing SageMaker embedding: {str(e)}")
            return False, f"Error: {str(e)}"

    @classmethod
    def _test_brclient_api_embedding(cls, model, text):
        """测试BR Client API嵌入模型"""
        try:
            headers = {"Content-Type": "application/json"}
            if model.api_key:
                headers["Authorization"] = f"Bearer {model.api_key}"
            
            # 构建请求体
            payload = {"input": text}  # 默认使用input字段而不是text字段
            if model.input_format:
                try:
                    input_format = json.loads(model.input_format)
                    payload = input_format
                    # 替换所有INPUT_TEXT占位符，不仅限于text字段
                    if isinstance(payload, dict):
                        for key in payload:
                            if isinstance(payload[key], str) and payload[key] == "INPUT_TEXT":
                                payload[key] = text
                except Exception as e:
                    logger.error(f"Error parsing input format: {str(e)}")
                    # 如果解析失败，回退到默认格式
                    payload = {"input": text}
            
            logger.info(f"Sending request to {model.api_url} with payload: {payload}")
            
            # 调用API
            response = requests.post(model.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # 解析响应
            response_body = response.json()
            logger.info(f"API response: {response_body}")
            
            # 尝试从不同的字段获取嵌入向量
            embedding = None
            if 'embedding' in response_body:
                embedding = response_body['embedding']
            elif 'embeddings' in response_body:
                embedding = response_body['embeddings']
            elif 'data' in response_body and isinstance(response_body['data'], list) and len(response_body['data']) > 0:
                # 处理可能的嵌套结构
                data_item = response_body['data'][0]
                if 'embedding' in data_item:
                    embedding = data_item['embedding']
                elif 'embeddings' in data_item:
                    embedding = data_item['embeddings']
            
            # 如果仍然找不到嵌入向量，记录错误
            if embedding is None:
                logger.error(f"Could not find embedding in response: {response_body}")
                return False, f"Error: Could not find embedding in response"
            
            # 处理嵌套列表
            if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
                embedding = embedding[0]  # 有些模型返回嵌套列表
            
            # 返回结果
            return True, {
                "embedding": embedding[:5] + ["..."] + embedding[-5:] if len(embedding) > 10 else embedding,
                "dimension": len(embedding),
                "model": model.name,
                "raw_response": response_body  # 添加原始响应以便调试
            }
        except Exception as e:
            logger.error(f"Error testing BR Client API embedding: {str(e)}")
            return False, f"Error: {str(e)}"

    @classmethod
    def get_global_setting(cls, key):
        """获取全局设置"""
        return cls.global_settings_dao.get_by_key(key)

    @classmethod
    def update_global_setting(cls, key, value, description=None):
        """更新全局设置"""
        setting = cls.global_settings_dao.get_by_key(key)
        if setting:
            desc = description if description is not None else setting.description
        else:
            desc = description or ""
        
        entity = GlobalSettingEntity(key, value, desc)
        cls.global_settings_dao.update(entity)
        logger.info(f"Global setting {key} updated to {value}")
        return True

    @classmethod
    def get_all_global_settings(cls):
        """获取所有全局设置"""
        settings = cls.global_settings_dao.get_all_settings()
        result = {}
        for setting in settings:
            result[setting.setting_key] = {
                'value': setting.setting_value,
                'description': setting.description
            }
        return result

    @classmethod
    def get_default_embedding_model(cls):
        """获取默认嵌入模型"""
        setting = cls.global_settings_dao.get_by_key('default_embedding_model')
        if setting and setting.setting_value:
            model = cls.embedding_model_dao.get_by_id(setting.setting_value)
            if model:
                return model
        
        # 如果没有设置默认模型或默认模型不存在，返回环境变量中的配置
        return embedding_info

    @classmethod
    def apply_default_embedding_model(cls):
        """应用默认嵌入模型到环境变量"""
        model = cls.get_default_embedding_model()
        if isinstance(model, EmbeddingModelEntity):
            # 更新环境变量中的嵌入模型信息
            embedding_info["embedding_platform"] = model.platform
            embedding_info["embedding_name"] = model.model_name
            embedding_info["embedding_dimension"] = model.dimension
            embedding_info["embedding_region"] = model.region
            embedding_info["br_client_url"] = model.api_url
            embedding_info["br_client_key"] = model.api_key
            logger.info(f"Applied default embedding model: {model.name}")
            return True
        return False

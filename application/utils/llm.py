import json
import boto3
import pandas as pd
import requests
from botocore.config import Config

from utils.domain import ModelResponse
from utils.logging import getLogger

from langchain_core.output_parsers import JsonOutputParser
from utils.prompts.generate_prompt import generate_llm_prompt, generate_agent_cot_system_prompt, \
    generate_intent_prompt, generate_knowledge_prompt, generate_data_visualization_prompt, \
    generate_agent_analyse_prompt, generate_data_summary_prompt, generate_suggest_question_prompt, \
    generate_query_rewrite_prompt

from utils.env_var import bedrock_ak_sk_info, BEDROCK_REGION, SAGEMAKER_EMBEDDING_REGION, \
    SAGEMAKER_SQL_REGION, embedding_info, AWS_DEFAULT_REGION
from utils.tool import convert_timestamps_to_str

from nlq.business.model import ModelManagement

logger = getLogger()

config = Config(
    region_name=BEDROCK_REGION,
    signature_version='v4',
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    },
    read_timeout=600
)
# model IDs are here:
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html

bedrock = None
json_parse = JsonOutputParser()
embedding_sagemaker_client = None
sagemaker_client = None


def get_bedrock_client(region=None, user_credentials=None):
    global bedrock
    
    # 添加详细日志
    if user_credentials:
        logger.info(f"User credentials provided for region {region}")
        if "access_key_id" in user_credentials and "secret_access_key" in user_credentials:
            logger.info("User credentials contain required fields")
        else:
            logger.warning("User credentials missing required fields")
    
    # 如果指定了区域或用户凭证，则创建新的客户端而不使用全局缓存
    if region or user_credentials:
        # 创建特定区域的配置
        custom_config = Config(
            region_name=region or BEDROCK_REGION,
            signature_version='v4',
            retries={'max_attempts': 10, 'mode': 'standard'},
            read_timeout=600
        )
        
        # 优先使用用户提供的凭证
        if user_credentials and "access_key_id" in user_credentials and "secret_access_key" in user_credentials:
            logger.info(f"Using user-provided credentials for Bedrock in region {region}")
            return boto3.client(
                service_name='bedrock-runtime', 
                config=custom_config,
                aws_access_key_id=user_credentials["access_key_id"],
                aws_secret_access_key=user_credentials["secret_access_key"]
            )
        elif len(bedrock_ak_sk_info) > 0:
            logger.info(f"Using Secrets Manager credentials for Bedrock in region {region}")
            return boto3.client(
                service_name='bedrock-runtime', 
                config=custom_config,
                aws_access_key_id=bedrock_ak_sk_info['access_key_id'],
                aws_secret_access_key=bedrock_ak_sk_info['secret_access_key']
            )
        else:
            logger.info(f"Using default credentials for Bedrock in region {region}")
            return boto3.client(service_name='bedrock-runtime', config=custom_config)
    
    # 使用全局缓存的客户端（默认区域）
    if not bedrock:
        if len(bedrock_ak_sk_info) == 0:
            bedrock = boto3.client(service_name='bedrock-runtime', config=config)
        else:
            bedrock = boto3.client(
                service_name='bedrock-runtime', config=config,
                aws_access_key_id=bedrock_ak_sk_info['access_key_id'],
                aws_secret_access_key=bedrock_ak_sk_info['secret_access_key'])
    return bedrock


def invoke_model_claude3(model_id, system_prompt, messages, max_tokens, with_response_stream=False):
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.01
        }
    )

    if with_response_stream:
        response = get_bedrock_client().invoke_model_with_response_stream(body=body, modelId=model_id)
        return response
    else:
        response = get_bedrock_client().invoke_model(body=body, modelId=model_id)
        response_body = json.loads(response.get('body').read())
        return response_body

def invoke_bedrock_anthropic_model(model_id, llm_region, input_payload, system_prompt, user_prompt, user_credentials=None):
    # 使用 get_bedrock_client 函数获取客户端，支持用户自定义凭证
    bedrock_invoke = get_bedrock_client(region=llm_region, user_credentials=user_credentials)
    input_payload = json.loads(input_payload)
    input_payload["system"] = system_prompt
    input_payload["messages"][0]["content"] = user_prompt
    model_id = model_id[len('bedrock-anthropic.'):]
    response = bedrock_invoke.invoke_model(modelId=model_id, body=json.dumps(input_payload))
    response_body = json.loads(response.get('body').read())
    return response_body


def invoke_bedrock_amazon_model(model_id, llm_region, input_payload, system_prompt, user_prompt, user_credentials=None):
    # 使用 get_bedrock_client 函数获取客户端，支持用户自定义凭证
    bedrock_invoke = get_bedrock_client(region=llm_region, user_credentials=user_credentials)
    input_payload = json.loads(input_payload)
    input_payload["system"][0]["text"] = system_prompt
    input_payload["messages"][0]["content"][0]["text"] = user_prompt
    model_id = model_id[len('bedrock-api-model.'):]
    response = bedrock_invoke.invoke_model(modelId=model_id, body=json.dumps(input_payload))
    response_body = json.loads(response.get('body').read())
    return response_body

def invoke_llama_70b(model_id, system_prompt, user_prompt, max_tokens, with_response_stream=False):
    """
    Invoke LLama-70B model
    :param model_id:
    :param system_prompt:
    :param messages:
    :param max_tokens:
    :param with_response_stream:
    :return:
    """
    try:
        llama3_prompt = """
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>

        {system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

        {user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
        body = {
            "prompt": llama3_prompt.format(system_prompt=system_prompt, user_prompt=user_prompt),
            "max_gen_len": 2048,
            "temperature": 0.01,
            "top_p": 0.9
        }
        if with_response_stream:
            response = get_bedrock_client().invoke_model_with_response_stream(body=json.dumps(body), modelId=model_id)
            return response
        else:
            response = get_bedrock_client().invoke_model(
                modelId=model_id, body=json.dumps(body)
            )
            response_body = json.loads(response["body"].read())
            return response_body
    except Exception as e:
        logger.error("Couldn't invoke LLama 70B")
        logger.error(e)


def invoke_mixtral_8x7b(model_id, system_prompt, messages, max_tokens, with_response_stream=False):
    """
    Invokes the Mixtral 8c7B model to run an inference using the input
    provided in the request body.

    :param prompt: The prompt that you want Mixtral to complete.
    :return: List of inference responses from the model.
    """

    try:
        instruction = f"<s>[INST] {system_prompt} \n The question you need to answer is: <question> {messages[0]['content']} </question>[/INST]"
        body = {
            "prompt": instruction,
            # "system": system_prompt,
            # "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.01,
        }

        if with_response_stream:
            response = get_bedrock_client().invoke_model_with_response_stream(body=json.dumps(body), modelId=model_id)
            return response
        else:
            response = get_bedrock_client().invoke_model(
                modelId=model_id, body=json.dumps(body)
            )
            response_body = json.loads(response["body"].read())
            response_body['content'] = response_body['outputs']
            return response_body
    except Exception as e:
        logger.error("Couldn't invoke Mixtral 8x7B")
        logger.error(e)
        raise


def get_embedding_sagemaker_client():
    global embedding_sagemaker_client
    if not embedding_sagemaker_client:
        if SAGEMAKER_EMBEDDING_REGION is not None and SAGEMAKER_EMBEDDING_REGION != "":
            embedding_sagemaker_client = boto3.client(service_name='sagemaker-runtime',
                                                      region_name=SAGEMAKER_EMBEDDING_REGION)
        else:
            embedding_sagemaker_client = boto3.client(service_name='sagemaker-runtime')
    return embedding_sagemaker_client


def get_sagemaker_client(model_region=""):
    global sagemaker_client
    if model_region != "" and model_region != AWS_DEFAULT_REGION:
        sagemaker_client = boto3.client(service_name='sagemaker-runtime',
                                        region_name=model_region)
        return sagemaker_client
    if not sagemaker_client:
        if SAGEMAKER_SQL_REGION is not None and SAGEMAKER_SQL_REGION != "":
            sagemaker_client = boto3.client(service_name='sagemaker-runtime',
                                            region_name=SAGEMAKER_SQL_REGION)
        else:
            sagemaker_client = boto3.client(service_name='sagemaker-runtime')
    return sagemaker_client


def invoke_model_sagemaker_endpoint(endpoint_name, body, model_type="LLM", with_response_stream=False, model_region=""):
    if with_response_stream:
        if model_type == "LLM":
            response = get_sagemaker_client(model_region).invoke_endpoint_with_response_stream(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
            return response
        else:
            response = get_embedding_sagemaker_client().invoke_endpoint_with_response_stream(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
        return response
    else:
        if model_type == "LLM":
            response = get_sagemaker_client(model_region).invoke_endpoint(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
            response_body = json.loads(response.get('Body').read())
            return response_body
        else:
            response = get_embedding_sagemaker_client().invoke_endpoint(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
            response_body = json.loads(response.get('Body').read())
            return response_body


def invoke_bedrock_api(api_url, headers, body, user_credentials=None):
    # 如果提供了用户凭证，可以在请求中添加认证信息
    if user_credentials and "access_key_id" in user_credentials and "secret_access_key" in user_credentials:
        # 这里可以根据API的需要添加认证信息
        # 例如，可以在headers中添加Authorization头
        logger.info("Using custom credentials for Bedrock API call")
        # 示例：如果API使用AWS签名V4
        # 这里只是一个示例，实际实现可能需要根据API的具体要求调整
        if "Authorization" not in headers:
            # 这里可以实现AWS签名V4逻辑，或者其他认证方式
            pass
    
    response = requests.post(api_url, headers=headers, data=json.dumps(body))
    return response.json()


def invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens=2048, with_response_stream=False):
    # Prompt with user turn only.
    user_message = {"role": "user", "content": user_prompt}
    messages = [user_message]
    logger.info(f'{system_prompt=}')
    logger.info(f'{messages=}')
    response = ""
    model_response = ModelResponse()

    model_config = {}
    if model_id.startswith('anthropic.claude-3'):
        response = invoke_model_claude3(model_id, system_prompt, messages, max_tokens, with_response_stream)
    elif model_id.startswith('bedrock-anthropic.'):
        model_config = ModelManagement.get_model_by_id(model_id)
        input_payload = model_config.input_payload
        llm_region = model_config.model_region
        
        # 检查是否有用户自定义凭证
        user_credentials = None
        if hasattr(model_config, 'input_format') and model_config.input_format:
            try:
                input_format_data = json.loads(model_config.input_format)
                if "credentials" in input_format_data and "access_key_id" in input_format_data["credentials"] and "secret_access_key" in input_format_data["credentials"]:
                    user_credentials = {
                        "access_key_id": input_format_data["credentials"]["access_key_id"],
                        "secret_access_key": input_format_data["credentials"]["secret_access_key"]
                    }
                    logger.info(f"Using custom credentials for model {model_id}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse credentials from input_format: {str(e)}")
        
        response = invoke_bedrock_anthropic_model(model_id, llm_region, input_payload, system_prompt, user_prompt, user_credentials)
    elif model_id.startswith('bedrock-api-model.'):
        model_config = ModelManagement.get_model_by_id(model_id)
        input_payload = model_config.input_payload
        llm_region = model_config.model_region
        
        # 检查是否有用户自定义凭证
        user_credentials = None
        if hasattr(model_config, 'input_format') and model_config.input_format:
            try:
                input_format_data = json.loads(model_config.input_format)
                if "credentials" in input_format_data and "access_key_id" in input_format_data["credentials"] and "secret_access_key" in input_format_data["credentials"]:
                    user_credentials = {
                        "access_key_id": input_format_data["credentials"]["access_key_id"],
                        "secret_access_key": input_format_data["credentials"]["secret_access_key"]
                    }
                    logger.info(f"Using custom credentials for model {model_id}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse credentials from input_format: {str(e)}")
        
        response = invoke_bedrock_amazon_model(model_id, llm_region, input_payload, system_prompt, user_prompt, user_credentials)
    elif model_id.startswith('mistral.mixtral-8x7b'):
        response = invoke_mixtral_8x7b(model_id, system_prompt, messages, max_tokens, with_response_stream)
    elif model_id.startswith('meta.llama3-70b'):
        response = invoke_llama_70b(model_id, system_prompt, user_prompt, max_tokens, with_response_stream)
    elif model_id.startswith('sagemaker.'):
        model_config = ModelManagement.get_model_by_id(model_id)
        prompt_template = model_config.prompt_template
        input_payload = model_config.input_payload
        llm_region = model_config.model_region
        prompt = prompt_template.replace("SYSTEM_PROMPT", system_prompt).replace("USER_PROMPT", user_prompt)
        input_payload = json.loads(input_payload)
        input_payload_text = json.dumps(input_payload, ensure_ascii=False)
        body = input_payload_text.replace("\"INPUT\"", json.dumps(prompt, ensure_ascii=False))
        logger.info(f'{body=}')
        endpoint_name = model_id[len('sagemaker.'):]
        response = invoke_model_sagemaker_endpoint(endpoint_name, body, "LLM", with_response_stream, llm_region)
    elif model_id.startswith('bedrock-api.'):
        model_config = ModelManagement.get_model_by_id(model_id)
        api_header = model_config.api_header
        input_payload = model_config.input_payload
        api_url = model_config.api_url
        
        # 检查是否有用户自定义凭证
        user_credentials = None
        if hasattr(model_config, 'input_format') and model_config.input_format:
            try:
                input_format_data = json.loads(model_config.input_format)
                if "credentials" in input_format_data and "access_key_id" in input_format_data["credentials"] and "secret_access_key" in input_format_data["credentials"]:
                    user_credentials = {
                        "access_key_id": input_format_data["credentials"]["access_key_id"],
                        "secret_access_key": input_format_data["credentials"]["secret_access_key"]
                    }
                    logger.info(f"Using custom credentials for Bedrock API model {model_id}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse credentials from input_format: {str(e)}")
                
        header = json.loads(api_header)
        body = json.loads(input_payload)
        body["system"] = system_prompt
        body["messages"][0]["content"] = user_prompt
        body["model_id"] = model_id[len('bedrock-api.'):]
        response = invoke_bedrock_api(api_url, header, body, user_credentials)
        header = json.loads(api_header)
        body = json.loads(input_payload)
        body["system"] = system_prompt
        body["messages"][0]["content"] = user_prompt
        body["model_id"] = model_id[len('bedrock-api.'):]
        response = invoke_bedrock_api(api_url, header, body)
    elif model_id.startswith('brclient-api.'):
        model_config = ModelManagement.get_model_by_id(model_id)
        api_header = model_config.api_header
        input_payload = model_config.input_payload
        api_url = model_config.api_url
        header = json.loads(api_header)
        body = json.loads(input_payload)
        body["messages"][0]["content"] = system_prompt
        body["messages"][1]["content"] = user_prompt
        response = invoke_bedrock_api(api_url, header, body)
    logger.info(f'{response=}')
    model_response.response = response
    if model_id.startswith('anthropic.claude-3') or model_id.startswith('bedrock-anthropic.') or model_id.startswith('bedrock-api-model.'):
        model_response.token_info = response.get("usage", {})
    else:
        model_response.token_info = {}
    if model_id.startswith('meta.llama3-70b'):
        model_response.text = response["generation"]
        return model_response
    elif model_id.startswith('sagemaker.'):
        output_format = model_config.output_format
        response = eval(output_format)
        model_response.text = response
        return model_response
    elif model_id.startswith('bedrock-api.') or model_id.startswith('brclient-api.'):
        output_format = model_config.output_format
        response = eval(output_format)
        model_response.text = response
        return model_response
    elif model_id.startswith('bedrock-anthropic.') or model_id.startswith('bedrock-api-model.'):
        output_format = model_config.output_format
        response = eval(output_format)
        model_response.text = response
        return model_response
    else:
        final_response = response.get("content")[0].get("text")
        model_response.text = final_response
        return model_response


def text_to_sql(ddl, hints, prompt_map, search_box, sql_examples=None, ner_example=None, model_id=None, dialect='mysql',
                model_provider=None, with_response_stream=False, additional_info='', environment_dict=None):
    user_prompt, system_prompt = generate_llm_prompt(ddl, hints, prompt_map, search_box, sql_examples, ner_example,
                                                     model_id, dialect=dialect, environment_dict=environment_dict)
    max_tokens = 4096
    model_response = invoke_llm_model(model_id, system_prompt, user_prompt + additional_info, max_tokens,
                                      with_response_stream)
    return model_response.text, model_response


def get_agent_cot_task(model_id, prompt_map, search_box, ddl, agent_cot_example=None, environment_dict=None):
    default_agent_cot_task = {"task_1": search_box}
    user_prompt, system_prompt = generate_agent_cot_system_prompt(ddl, prompt_map, search_box, model_id,
                                                                  agent_cot_example, environment_dict)
    try:
        max_tokens = 2048
        model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        final_response = model_response.text
        logger.info(f'{final_response=}')
        intent_result_dict = json_parse.parse(final_response)
        return intent_result_dict, model_response
    except Exception as e:
        logger.error("get_agent_cot_task is error:{}".format(e))
        return default_agent_cot_task


def data_analyse_tool(model_id, prompt_map, search_box, sql_data, search_type, environment_dict=None):
    try:
        max_tokens = 2048
        if search_type == "agent":
            user_prompt, system_prompt = generate_agent_analyse_prompt(prompt_map, search_box, model_id, sql_data,
                                                                       environment_dict)
        else:
            user_prompt, system_prompt = generate_data_summary_prompt(prompt_map, search_box, model_id, sql_data,
                                                                      environment_dict)
        model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        final_response = model_response.text
        logger.info(f'{final_response=}')
        return final_response, model_response
    except Exception as e:
        logger.error("data_analyse_tool is error")


def get_query_intent(model_id, search_box, prompt_map, environment_dict=None):
    default_intent = {"intent": "normal_search"}

    user_prompt, system_prompt = generate_intent_prompt(prompt_map, search_box, model_id, environment_dict)
    max_tokens = 2048
    model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
    final_response = model_response.text
    logger.info(f'{final_response=}')
    intent_result_dict = json_parse.parse(final_response)
    return intent_result_dict, model_response


def get_query_rewrite(model_id, search_box, prompt_map, chat_history, environment_dict=None):
    query_rewrite = {"intent": "original_problem", "query": search_box}
    history_query = "\n".join(chat_history)
    user_prompt, system_prompt = generate_query_rewrite_prompt(prompt_map, search_box, model_id, history_query,
                                                               environment_dict)
    max_tokens = 2048
    model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
    final_response = model_response.text
    logger.info(f'{final_response=}')
    query_rewrite_result = json_parse.parse(final_response)
    return query_rewrite_result, model_response


def knowledge_search(model_id, search_box, prompt_map, environment_dict=None, entity_info=None):
    # 创建环境字典的副本，以便我们可以添加实体信息
    if environment_dict is None:
        environment_dict = {}
    else:
        environment_dict = environment_dict.copy()
    
    # 如果有实体信息，构建实体信息字符串
    entity_info_str = ""
    if entity_info and len(entity_info) > 0:
        entity_info_str = "\n\n相关实体信息：\n"
        for entity in entity_info:
            entity_source = entity.get("_source", {})
            entity_name = entity_source.get("entity", "")
            entity_comment = entity_source.get("comment", "")
            entity_type = entity_source.get("entity_type", "")
            entity_info_str += f"- 实体名称: {entity_name}, 类型: {entity_type}, 描述: {entity_comment}\n"
    
    # 将实体信息添加到环境字典中
    environment_dict["entity_info"] = entity_info_str
    
    # 生成提示并调用模型
    user_prompt, system_prompt = generate_knowledge_prompt(prompt_map, search_box, model_id, environment_dict)
    max_tokens = 2048
    model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
    final_response = model_response.text
    return final_response, model_response


def select_data_visualization_type(model_id, search_box, search_data, prompt_map, environment_dict=None):
    default_data_visualization = {
        "show_type": "table",
        "format_data": []
    }
    try:
        user_prompt, system_prompt = generate_data_visualization_prompt(prompt_map, search_box, search_data, model_id,
                                                                        environment_dict)
        max_tokens = 2048
        model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        final_response = model_response.text
        data_visualization_dict = json_parse.parse(final_response)
        return data_visualization_dict, model_response
    except Exception as e:
        logger.error("select_data_visualization_type is error {}", e)
        return default_data_visualization


def data_visualization(model_id, search_box, search_data, prompt_map, environment_dict=None):
    model_response = ModelResponse()
    model_response.token_info = {}
    if len(search_data) == 0:
        return "table", [], "-1", [], model_response
    if isinstance(search_data, pd.DataFrame):
        search_data = search_data.fillna("")
        columns = list(search_data.columns)
        data_list = search_data.values.tolist()
        all_columns_data = [columns] + data_list
    else:
        all_columns_data = search_data
        columns = all_columns_data[0]
        search_data = pd.DataFrame(search_data[1:], columns=search_data[0])
        if len(search_data) == 0:
            return "table", search_data, "-1", [], model_response
    all_columns_data = convert_timestamps_to_str(all_columns_data)
    try:
        if len(all_columns_data) < 1:
            return "table", all_columns_data, "-1", [], model_response
        else:
            if len(all_columns_data) > 10:
                all_columns_data_sample = all_columns_data[0:3]
            else:
                all_columns_data_sample = all_columns_data[0:3]
            logger.info("before data_visualization:")
            model_select_type_dict, model_response = select_data_visualization_type(model_id, search_box,
                                                                                    all_columns_data_sample,
                                                                                    prompt_map, environment_dict)
            logger.info("after data_visualization:")
            model_select_type = model_select_type_dict["show_type"]
            model_select_type_columns = model_select_type_dict["format_data"][0]
            data_list = search_data[model_select_type_columns].values.tolist()

            # 返回格式校验
            if len(columns) > 2:
                if model_select_type == "table":
                    logger.info("return data_visualization:")
                    return "table", all_columns_data, "bar", all_columns_data, model_response
                else:
                    if len(model_select_type_columns) == 2:
                        reindex_columns = model_select_type_columns + [col for col in columns if
                                                                       col not in model_select_type_columns]
                        reindex_data = search_data[reindex_columns].values.tolist()
                        logger.info("return data_visualization:")
                        return "table", all_columns_data, model_select_type, [
                                                                                 reindex_columns] + reindex_data, model_response
                    else:
                        return "table", all_columns_data, "bar", all_columns_data, model_response
            elif len(columns) == 2:
                if model_select_type == "table":
                    return "table", all_columns_data, "bar", all_columns_data, model_response
                else:
                    return model_select_type, [model_select_type_columns] + data_list, "-1", [], model_response
            else:
                return "table", all_columns_data, "-1", [], model_response
    except Exception as e:
        logger.error("data_visualization is error {}", e)
        model_response = ModelResponse()
        model_response.token_info = {}
        return "table", all_columns_data, "-1", [], model_response


def create_vector_embedding(text, index_name):
    """
    重定向到nlq/business/vector_store.py中的create_vector_embedding函数
    """
    try:
        # 导入VectorStore类
        from nlq.business.vector_store import VectorStore
        
        # 调用VectorStore中的create_vector_embedding函数
        logger.info(f"Redirecting to VectorStore.create_vector_embedding for text: {text[:30]}...")
        vector_field = VectorStore.create_vector_embedding(text)
        
        # 返回与原函数相同格式的结果
        return {"_index": index_name, "text": text, "vector_field": vector_field}
    except Exception as e:
        logger.error(f"Error in create_vector_embedding redirection: {str(e)}")
        # 返回一个默认的空向量
        return {"_index": index_name, "text": text, "vector_field": [0.0] * int(embedding_info.get("embedding_dimension", 1536))}


def create_vector_embedding_with_br_client_api(text, index_name, model_name):

    api_url = embedding_info["br_client_url"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + embedding_info["br_client_key"]
    }
    body = {
            "model": model_name,
            "input": text
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(body))
    response_info = response.json()
    embedding = response_info['data']['embedding']
    return {"_index": index_name, "text": text, "vector_field": embedding}

def create_vector_embedding_with_bedrock(text, index_name, model_name):
    payload = {"inputText": f"{text}"}
    body = json.dumps(payload)
    modelId = model_name
    accept = "application/json"
    contentType = "application/json"

    response = get_bedrock_client().invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    embedding = response_body.get("embedding")
    return {"_index": index_name, "text": text, "vector_field": embedding}


def create_vector_embedding_with_sagemaker(endpoint_name, text, index_name):
    try:
        if not endpoint_name:
            logger.error("SageMaker endpoint name is None or empty")
            # 返回一个默认的空向量
            return {"_index": index_name, "text": text, "vector_field": [0.0] * int(embedding_info.get("embedding_dimension", 1536))}
            
        # 使用正确的请求格式 - 根据AmazonQ.md分析
        body = json.dumps(
            {
                "input": text
            }
        )
        
        logger.info(f"Calling embedding endpoint {endpoint_name} with body: {body}")
        response = invoke_model_sagemaker_endpoint(endpoint_name, body, model_type="embedding")
        
        # 处理响应 - 根据测试结果分析
        if isinstance(response, dict) and 'data' in response:
            # 处理嵌套结构 - EMD-Model-bge-m3-endpoint返回格式
            data = response.get('data', [])
            if isinstance(data, list) and len(data) > 0:
                embedding_data = data[0]
                if isinstance(embedding_data, dict) and 'embedding' in embedding_data:
                    embeddings = embedding_data['embedding']
                    logger.info(f"Successfully extracted embedding from data[0]['embedding'], dimension: {len(embeddings)}")
                    return {"_index": index_name, "text": text, "vector_field": embeddings}
        
        # 如果上面的格式不匹配，尝试其他可能的格式
        if isinstance(response, dict) and 'embedding' in response:
            embeddings = response['embedding']
            return {"_index": index_name, "text": text, "vector_field": embeddings}
        elif isinstance(response, list):
            embeddings = response[0] if len(response) > 0 else []
            return {"_index": index_name, "text": text, "vector_field": embeddings}
        
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
            logger.info(f"Retrying embedding endpoint {endpoint_name} with body: {body}")
            response = invoke_model_sagemaker_endpoint(endpoint_name, body, model_type="embedding")
            
            if isinstance(response, list):
                embeddings = response[0]
            else:
                embeddings = response
                
            return {"_index": index_name, "text": text, "vector_field": embeddings}
        except Exception as retry_error:
            logger.error(f"Retry also failed: {str(retry_error)}")
            # 返回一个默认的空向量
            return {"_index": index_name, "text": text, "vector_field": [0.0] * int(embedding_info.get("embedding_dimension", 1536))}
            
    except Exception as e:
        logger.error(f"Error in create_vector_embedding_with_sagemaker: {str(e)}")
        # 返回一个默认的空向量
        return {"_index": index_name, "text": text, "vector_field": [0.0] * int(embedding_info.get("embedding_dimension", 1536))}


def generate_suggested_question(prompt_map, search_box, model_id=None, environment_dict=None):
    max_tokens = 2048
    user_prompt, system_prompt = generate_suggest_question_prompt(prompt_map, search_box, model_id, environment_dict)
    model_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens)
    final_response = model_response.text
    return final_response, model_response

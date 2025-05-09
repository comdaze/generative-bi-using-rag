import json
import boto3
import streamlit as st
from botocore.config import Config
from utils.logging import getLogger
from config_files.language_config import get_text
from nlq.business.model import ModelManagement

logger = getLogger()

def bedrock_model_connect(bedrock_model_name_id, bedrock_region, system_prompt, user_prompt, input_payload, output_format, user_credentials=None):
    """
    使用 Bedrock Converse API 连接到任何 Bedrock 模型。
    
    Args:
        bedrock_model_name_id (str): 模型 ID
        bedrock_region (str): Bedrock 区域
        input_payload (str): 包含输入负载模板的 JSON 字符串
        output_format (str): 提取响应的字符串表达式
        user_credentials (dict, optional): 用户 AWS 凭证
        
    Returns:
        tuple: (success_flag, response_or_error)
    """
    try:
        # 处理模型 ID 前缀
        original_model_id = bedrock_model_name_id
        if bedrock_model_name_id.startswith("bedrock-model."):
            bedrock_model_name_id = bedrock_model_name_id[14:]  # 移除前缀
        
            
        # 记录连接详情
        logger.info(f"Connecting to Bedrock in region {bedrock_region}")
        logger.info(f"Original model ID: {original_model_id}, Processed model ID: {bedrock_model_name_id}")
        logger.info(f"Using custom credentials: {user_credentials is not None}")
        
        # 如果提供了凭证，记录凭证详情
        if user_credentials:
            has_ak = 'access_key_id' in user_credentials and bool(user_credentials['access_key_id'])
            has_sk = 'secret_access_key' in user_credentials and bool(user_credentials['secret_access_key'])
            logger.info(f"Credentials contain valid access_key_id: {has_ak}")
            logger.info(f"Credentials contain valid secret_access_key: {has_sk}")
            if has_ak and has_sk:
                logger.info(f"Access key first 4 chars: {user_credentials['access_key_id'][:4]}...")
                logger.info(f"Access key length: {len(user_credentials['access_key_id'])}")
                logger.info(f"Secret key length: {len(user_credentials['secret_access_key'])}")
        
        # 使用适当的凭证创建 Bedrock 客户端
        if (user_credentials and 
            'access_key_id' in user_credentials and user_credentials['access_key_id'] and 
            'secret_access_key' in user_credentials and user_credentials['secret_access_key']):
            
            logger.info(f"Creating Bedrock client with user credentials in region {bedrock_region}")
            config = Config(region_name=bedrock_region, signature_version='v4',
                            retries={
                                'max_attempts': 10,
                                'mode': 'standard'
                            }, read_timeout=600)
            
            bedrock = boto3.client(
                service_name='bedrock-runtime', 
                config=config,
                aws_access_key_id=user_credentials["access_key_id"],
                aws_secret_access_key=user_credentials["secret_access_key"]
            )
            logger.info("Bedrock client created with user credentials")
        else:
            # 使用默认凭证
            logger.info(f"Creating Bedrock client with default credentials in region {bedrock_region}")
            config = Config(region_name=bedrock_region, signature_version='v4',
                            retries={
                                'max_attempts': 10,
                                'mode': 'standard'
                            }, read_timeout=600)
            bedrock = boto3.client(service_name='bedrock-runtime', config=config)
            logger.info("Bedrock client created with default credentials")

        # 解析输入负载
        try:
            input_payload = json.loads(input_payload)
            logger.info(f"Input payload parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse input payload: {str(e)}")
            return False, f"Invalid JSON in input payload: {str(e)}"
        
        # # 准备测试提示
        # system_prompt = "You are a human friendly conversation assistant."
        # user_prompt = "Hello, who are you"
        
        # 创建 Converse API 请求 - 使用正确的格式
        system = [{"text": system_prompt}]
        messages = [
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ]
        
        # 从输入负载中提取参数
        inference_config = {}
        if "temperature" in input_payload:
            inference_config["temperature"] = input_payload.get("temperature", 0.01)
        elif "inferenceConfig" in input_payload and "temperature" in input_payload["inferenceConfig"]:
            inference_config["temperature"] = input_payload["inferenceConfig"].get("temperature", 0.01)
        else:
            inference_config["temperature"] = 0.01
            
        if "max_tokens" in input_payload:
            inference_config["maxTokens"] = input_payload.get("max_tokens", 2048)
        elif "maxTokens" in input_payload:
            inference_config["maxTokens"] = input_payload.get("maxTokens", 2048)
        elif "inferenceConfig" in input_payload and "max_new_tokens" in input_payload["inferenceConfig"]:
            inference_config["maxTokens"] = input_payload["inferenceConfig"].get("max_new_tokens", 2048)
        else:
            inference_config["maxTokens"] = 2048
            
        if "top_p" in input_payload:
            inference_config["topP"] = input_payload.get("top_p", 0.9)
        elif "topP" in input_payload:
            inference_config["topP"] = input_payload.get("topP", 0.9)
        elif "inferenceConfig" in input_payload and "top_p" in input_payload["inferenceConfig"]:
            inference_config["topP"] = input_payload["inferenceConfig"].get("top_p", 0.9)
        else:
            inference_config["topP"] = 0.9
            
        logger.info(f"Using inference config: {inference_config}")
        logger.info(f"Using system: {system}")
        logger.info(f"Using messages: {messages}")
        
        # 调用 Converse API
        logger.info(f"Invoking Bedrock model with Converse API: {bedrock_model_name_id}")
        try:
            response_info = bedrock.converse(
                modelId=bedrock_model_name_id,
                system=system,
                messages=messages,
                inferenceConfig=inference_config
            )
            logger.info(f"Converse API call successful")
            
            # 提取响应 - 使用正确的格式
            try:
                # 使用提供的输出格式提取答案，如果没有提供则使用默认格式
                if not output_format or output_format == "":
                    answer = response_info["output"]["message"]["content"][0]["text"]
                else:
                    # 将response_info赋值给response变量，以便使用output_format
                    response = response_info
                    answer = eval(output_format)
                
                return True, answer
            except Exception as e:
                logger.error(f"Failed to extract answer: {str(e)}")
                # 返回原始响应
                return True, str(response_info)
                
        except Exception as e:
            logger.error(f"Converse API call failed: {str(e)}")
            
            # 尝试使用传统的 invoke_model 作为备选方案
            logger.info(f"Falling back to invoke_model API")
            try:
                # 根据模型类型准备请求体
                if "anthropic" in bedrock_model_name_id.lower() or "claude" in bedrock_model_name_id.lower():
                    body = json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": inference_config.get("maxTokens", 2048),
                        "temperature": inference_config.get("temperature", 0.01),
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}]
                    })
                elif "amazon" in bedrock_model_name_id.lower() or "titan" in bedrock_model_name_id.lower():
                    body = json.dumps({
                        "inputText": f"System: {system_prompt}\n\nHuman: {user_prompt}",
                        "textGenerationConfig": {
                            "maxTokenCount": inference_config.get("maxTokens", 2048),
                            "temperature": inference_config.get("temperature", 0.01),
                            "topP": inference_config.get("topP", 0.9)
                        }
                    })
                else:
                    # 使用原始输入负载作为备选
                    body = json.dumps(input_payload)
                
                response_info = bedrock.invoke_model(body=body, modelId=bedrock_model_name_id)
                response = json.loads(response_info.get('body').read())
                
                # 尝试使用提供的输出格式提取答案
                try:
                    answer = eval(output_format)
                    return True, answer
                except Exception as eval_error:
                    logger.error(f"Failed to extract answer using output format: {str(eval_error)}")
                    # 返回原始响应
                    return True, str(response)
                
            except Exception as invoke_error:
                logger.error(f"invoke_model API call also failed: {str(invoke_error)}")
                return False, f"Both Converse API and invoke_model API failed: {str(e)}, then {str(invoke_error)}"
    
    except Exception as e:
        logger.error(f"Failed to connect: {str(e)}")
        return False, str(e)

def test_bedrock_model_connect(bedrock_model_name_id, bedrock_region, input_payload, output_format):
    """
    测试 Bedrock 模型连接的函数。
    使用 Converse API 替代特定模型的连接函数。
    """
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language), key="test_bedrock_model_btn"):
        if bedrock_model_name_id == '':
            st.error(get_text("required_error", language).format(get_text("model_id", language)))
        elif bedrock_region == '':
            st.error(get_text("required_error", language).format(get_text("model_region", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        
        # 记录会话状态键，帮助调试
        logger.info(f"Session state keys: {list(st.session_state.keys())}")
        
        # 从会话状态获取凭证
        user_credentials = None
        access_key = ''
        secret_key = ''
        
        # 检查更新表单的凭证
        if 'update_model_ak' in st.session_state and st.session_state.get('update_model_ak'):
            access_key = st.session_state.get('update_model_ak')
            secret_key = st.session_state.get('update_model_sk', '')
            logger.info(f"Found credentials in update form - AK length: {len(access_key)}, SK exists: {bool(secret_key)}")
        
        # 如果更新表单没有凭证，则检查新建表单
        if not (access_key and secret_key):
            # 检查各种可能的会话状态键
            possible_ak_keys = ['llm_new_model_ak', 'llm_new_amazon_ak', 'llm_new_anthropic_ak', 'llm_new_bedrock_ak']
            possible_sk_keys = ['llm_new_model_sk', 'llm_new_amazon_sk', 'llm_new_anthropic_sk', 'llm_new_bedrock_sk']
            
            for ak_key in possible_ak_keys:
                if ak_key in st.session_state and st.session_state.get(ak_key):
                    access_key = st.session_state.get(ak_key)
                    # 找到对应的 SK
                    for sk_key in possible_sk_keys:
                        if sk_key in st.session_state and st.session_state.get(sk_key):
                            secret_key = st.session_state.get(sk_key)
                            break
                    break
            
            if access_key and secret_key:
                logger.info(f"Found credentials in new form - AK length: {len(access_key)}, SK exists: {bool(secret_key)}")
        
        # 创建凭证对象
        if access_key and secret_key:
            user_credentials = {
                "access_key_id": access_key,
                "secret_access_key": secret_key
            }
            logger.info(f"Created credentials object with valid AK and SK")
        else:
            logger.info(f"No valid credentials found in session state")
        
        # 准备测试提示
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        # 调用测试函数
        connect_flag, connect_info = bedrock_model_connect(
            bedrock_model_name_id, 
            bedrock_region, 
            system_prompt,
            user_prompt,
            input_payload, 
            output_format, 
            user_credentials
        )
        
        if connect_flag:
            st.success(get_text("connected_successfully", language))
        else:
            st.error(get_text("failed_to_connect", language))
        st.write(connect_info)

def display_new_bedrock_model():
    """
    显示创建新的 Bedrock 模型的表单。
    使用统一的 Converse API 接口。
    """
    language = st.session_state.get('language', 'en')
    
    # 根据模型类型提供默认的输入负载模板
    model_sub_type = st.selectbox(
        get_text("Model Sub Type", language),  # 使用多语言支持
        ["Converse API", "Amazon", "Anthropic", "Meta", "Mistral", "Cohere"],
        key="llm_new_sub_model_type"
    )
    
    # 根据选择的模型类型提供默认模板
    if model_sub_type == "Amazon":
        system_list = [{"text": "SYSTEM_PROMPT"}]
        message_list = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
        inf_params = {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.01}
        example_input = {
            "schemaVersion": "messages-v1",
            "messages": message_list,
            "system": system_list,
            "inferenceConfig": inf_params,
        }
        default_output = "response['output']['message']['content'][0]['text']"
    elif model_sub_type == "Anthropic":
        system = [{"text": "SYSTEM_PROMPT"}]
        messages = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
        example_input = {
            "system": system,
            "messages": messages,
            "inferenceConfig": {
                "temperature": 0.01,
                "maxTokens": 2048,
                "topP": 0.9
            }
        }
        default_output = "response['output']['message']['content'][0]['text']"
    elif model_sub_type in ["Meta", "Mistral", "Cohere"]:
        system = [{"text": "SYSTEM_PROMPT"}]
        messages = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
        example_input = {
            "system": system,
            "messages": messages,
            "inferenceConfig": {
                "temperature": 0.01,
                "maxTokens": 2048,
                "topP": 0.9
            }
        }
        default_output = "response['output']['message']['content'][0]['text']"
    else:
        # 通用模板 - 使用Converse API格式
        system = [{"text": "SYSTEM_PROMPT"}]
        messages = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
        example_input = {
            "system": system,
            "messages": messages,
            "inferenceConfig": {
                "temperature": 0.01,
                "maxTokens": 2048,
                "topP": 0.9
            }
        }
        default_output = "response['output']['message']['content'][0]['text']"

    # 模型信息输入
    bedrock_model_name = st.text_input(get_text("model_id", language), key="llm_new_bedrock_name")
    bedrock_region = st.text_input(get_text("model_region", language), key="llm_new_bedrock_region")

    # 添加用户自定义凭证(AK/SK)输入字段
    access_key = st.text_input("Access Key ID(Optional)", type="password", key="llm_new_model_ak")
    secret_key = st.text_input("Secret Access Key(Optional)", type="password", key="llm_new_model_sk")
    
    # 记录凭证状态
    if access_key and secret_key:
        logger.info(f"Credentials entered in form - AK length: {len(access_key)}, SK length: {len(secret_key)}")
    

    
    input_payload = st.text_area(
        get_text("input_payload", language), 
        value=json.dumps(example_input, indent=2),
        height=200,
        help=get_text("input_payload_help", language),
        key="llm_new_bedrock_payload"
    )

    output_format = st.text_area(
        get_text("output_format", language),
        value=default_output,
        placeholder=get_text("output_format_placeholder", language),
        height=100,
        help=get_text("output_format_help", language),
        key="llm_new_bedrock_output"
    )
    
    # 将用户凭证转换为JSON格式
    input_format = ""
    if access_key and secret_key:
        input_format = json.dumps({
            "credentials": {
                "access_key_id": access_key,
                "secret_access_key": secret_key
            }
        })
        logger.info("User credentials prepared for new Bedrock model")
        
        # 验证JSON格式
        try:
            parsed = json.loads(input_format)
            logger.info(f"Credentials JSON valid: {bool(parsed.get('credentials', {}).get('access_key_id'))}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
    
    # 测试连接按钮
    test_bedrock_model_connect(bedrock_model_name, bedrock_region, input_payload, output_format)
    
    # 添加模型按钮
    if st.button(get_text("add_connection", language), type='primary', key="llm_add_bedrock_btn"):
        if bedrock_model_name == '':
            st.error(get_text("required_error", language).format(get_text("model_id", language)))
        elif bedrock_region == '':
            st.error(get_text("required_error", language).format(get_text("model_region", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        else:
            # 根据模型类型确定模型ID前缀
            model_prefix = "bedrock-model"   
            model_id = f"{model_prefix}.{bedrock_model_name}"
            
            # 添加模型
            ModelManagement.add_bedrock_model(
                model_id=model_id,
                model_region=bedrock_region, 
                input_payload=input_payload,
                output_format=output_format,
                input_format=input_format  # 添加用户凭证
            )
            st.success(get_text("added_successfully", language).format(bedrock_model_name))
            
            # 更新会话状态
            if 'model_list' in st.session_state:
                st.session_state.model_list.append(model_id)
            st.session_state.llm_new_model = False
            
            # 更新提示模板
            with st.spinner(get_text("update_prompt", language)):
                update_profile_prompts(bedrock_model_name)
                st.success(get_text("prompt_added_successfully", language))
                
                # 刷新模型列表和配置文件
                if 'model_list' in st.session_state:
                    st.session_state.model_list = ModelManagement.get_all_models()
                if 'profiles' in st.session_state:
                    from nlq.business.profile import ProfileManagement
                    st.session_state.profiles = ProfileManagement.get_all_profiles_with_info()
                st.success(get_text("profiles_update_successfully", language))

def display_update_bedrock_model(current_model):
    """
    显示更新现有 Bedrock 模型的表单。
    使用统一的 Converse API 接口。
    """
    language = st.session_state.get('language', 'en')
    
    # 显示模型信息
    api_model_name = st.text_input(
        get_text("model_id", language), 
        current_model.model_id, 
        disabled=True,
        key="update_bedrock_name"
    )
    bedrock_region = st.text_input(
        get_text("model_region", language), 
        current_model.model_region, 
        disabled=True,
        key="update_bedrock_region"
    )
    input_payload = st.text_area(
        get_text("input_payload", language), 
        current_model.input_payload, 
        height=200,
        key="update_bedrock_payload"
    )
    output_format = st.text_area(
        get_text("output_format", language), 
        current_model.output_format, 
        height=100,
        key="update_bedrock_output"
    )
    
    # 尝试从input_format中提取现有凭证
    existing_credentials = {"access_key_id": "", "secret_access_key": ""}
    if hasattr(current_model, 'input_format') and current_model.input_format:
        try:
            input_data = json.loads(current_model.input_format)
            if "credentials" in input_data:
                existing_credentials = input_data["credentials"]
                logger.info("Found existing credentials in input_format")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
    
    # 显示凭证输入字段
    access_key = st.text_input(
        "Access Key ID", 
        value=existing_credentials.get("access_key_id", ""),
        type="password", 
        key="update_model_ak"
    )
    secret_key = st.text_input(
        "Secret Access Key", 
        value=existing_credentials.get("secret_access_key", ""),
        type="password", 
        key="update_model_sk"
    )
    
    # 将用户凭证转换为JSON格式
    input_format = ""
    if access_key and secret_key:
        input_format = json.dumps({
            "credentials": {
                "access_key_id": access_key,
                "secret_access_key": secret_key
            }
        })
        logger.info("User credentials prepared for updating Bedrock model")
    
    # 测试连接按钮
    test_bedrock_model_connect(api_model_name, bedrock_region, input_payload, output_format)
    
    # 更新模型按钮
    if st.button(get_text("update_model_connection", language), type='primary', key="update_bedrock_btn"):
        ModelManagement.update_model(
            model_id=api_model_name, 
            model_region=bedrock_region,
            prompt_template="", 
            input_payload=input_payload,
            output_format=output_format, 
            api_url="", 
            api_header="",
            input_format=input_format  # 添加用户凭证
        )
        st.success(get_text("updated_successfully", language).format(api_model_name))

def update_profile_prompts(model_name):
    """
    更新所有配置文件的模型提示。
    """
    from nlq.business.profile import ProfileManagement
    
    all_profiles = ProfileManagement.get_all_profiles_with_info()
    for profile_name, profile_value in all_profiles.items():
        profile_prompt_map = profile_value["prompt_map"]
        update_prompt_map = {}
        for each_process in profile_prompt_map:
            update_prompt_map[each_process] = profile_prompt_map[each_process]
            update_prompt_map[each_process]["system_prompt"][model_name] = \
                profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
            update_prompt_map[each_process]["user_prompt"][model_name] = \
                profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
        ProfileManagement.update_prompt_map(profile_name, update_prompt_map)

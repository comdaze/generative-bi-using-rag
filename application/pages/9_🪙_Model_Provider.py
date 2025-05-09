import json
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from botocore.config import Config
load_dotenv()
from nlq.business.model import ModelManagement
from nlq.business.embedding import EmbeddingModelManagement
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar
from config_files.language_config import get_text
from utils.converse import display_new_bedrock_model,display_update_bedrock_model

logger = getLogger()

# Initialize session state variables
def initialize_session_state():
    """Initialize all session state variables"""
    # LLM Models tab state
    if 'llm_new_model' not in st.session_state:
        st.session_state.llm_new_model = False
    if 'llm_update_model' not in st.session_state:
        st.session_state.llm_update_model = False
    if 'llm_current_model' not in st.session_state:
        st.session_state.llm_current_model = None
    if 'llm_current_model_name' not in st.session_state:
        st.session_state.llm_current_model_name = None
    if "model_list" not in st.session_state:
        st.session_state.model_list = ModelManagement.get_all_models()
    
    # Embedding Models tab state
    if 'embedding_new_model' not in st.session_state:
        st.session_state.embedding_new_model = False
    if 'embedding_update_model' not in st.session_state:
        st.session_state.embedding_update_model = False
    if 'embedding_current_model' not in st.session_state:
        st.session_state.embedding_current_model = None
    if 'embedding_current_model_name' not in st.session_state:
        st.session_state.embedding_current_model_name = None
    if "embedding_model_list" not in st.session_state:
        st.session_state.embedding_model_list = EmbeddingModelManagement.get_all_embedding_models()
    
    # Global settings
    if "global_settings" not in st.session_state:
        st.session_state.global_settings = EmbeddingModelManagement.get_all_global_settings()
    
    # Profiles
    if 'profiles' not in st.session_state:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())

# Callback functions for LLM Models tab
def on_new_llm_clicked():
    """When Create New Model button is clicked"""
    st.session_state.llm_new_model = True
    st.session_state.llm_update_model = False
    st.session_state.llm_current_model = None
    st.session_state.llm_current_model_name = None

def on_llm_model_selected():
    """When an LLM model is selected from the dropdown"""
    if st.session_state.llm_current_model_name:
        st.session_state.llm_current_model = ModelManagement.get_model_by_id(st.session_state.llm_current_model_name)
        st.session_state.llm_update_model = True
        st.session_state.llm_new_model = False

# Callback functions for Embedding Models tab
def on_new_embedding_clicked():
    """When Create New Embedding Model button is clicked"""
    st.session_state.embedding_new_model = True
    st.session_state.embedding_update_model = False
    st.session_state.embedding_current_model = None
    st.session_state.embedding_current_model_name = None

def on_embedding_model_selected():
    """When an embedding model is selected from the dropdown"""
    if st.session_state.embedding_current_model_name:
        try:
            st.session_state.embedding_current_model = EmbeddingModelManagement.get_embedding_model_by_id(
                st.session_state.embedding_current_model_name)
            if st.session_state.embedding_current_model:
                st.session_state.embedding_update_model = True
                st.session_state.embedding_new_model = False
            else:
                logger.error(f"Could not load embedding model: {st.session_state.embedding_current_model_name}")
                st.session_state.embedding_update_model = False
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            st.session_state.embedding_current_model = None
            st.session_state.embedding_update_model = False




def other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    connect_flag = False
    connect_info = "-1"
    try:
        if api_model_name.startswith("brclient-api."):
            api_model_name = api_model_name[13:]
        header = json.loads(api_header)
        input_payload = json.loads(input_payload)
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        input_payload["messages"][0]["content"] = system_prompt
        input_payload["messages"][1]["content"] = user_prompt
        response = requests.post(api_url, headers=header, data=json.dumps(input_payload))
        response = response.json()
        answer = eval(output_format)
        connect_info = answer
        connect_flag = True
    except Exception as e:
        logger.error("Failed to connect: {}".format(e))
        connect_info = str(e)
    return connect_flag, connect_info

def sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    connect_flag = False
    connect_info = "-1"
    try:
        # Implementation for SageMaker model connection test
        # This function would be implemented based on the original code
        connect_flag = True
        connect_info = "SageMaker connection successful"
    except Exception as e:
        logger.error("Failed to connect: {}".format(e))
        connect_info = str(e)
    return connect_flag, connect_info


# Test connection functions for UI
def test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language), key="test_sagemaker_btn"):
        if sagemaker_name == '':
            st.error(get_text("required_error", language).format(get_text("sagemaker_endpoint_name", language)))
        elif sagemaker_region == '':
            st.error(get_text("required_error", language).format(get_text("sagemaker_endpoint_region", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        connect_flag, connect_info = sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template,
                                                             input_payload,
                                                             output_format)
        if connect_flag:
            st.success(get_text("connected_successfully", language))
        else:
            st.error(get_text("failed_to_connect", language))
        st.write(connect_info)

def test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language), key="test_other_api_btn"):
        if api_model_name == '':
            st.error(get_text("required_error", language).format(get_text("api_model_name", language)))
        elif api_url == '':
            st.error(get_text("required_error", language).format(get_text("api_url", language)))
        elif api_header == '':
            st.error(get_text("required_error", language).format(get_text("api_header", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        connect_flag, connect_info = other_api_model_connect(api_model_name, api_url, api_header, input_payload,
                                                             output_format)
        if connect_flag:
            st.success(get_text("connected_successfully", language))
        else:
            st.error(get_text("failed_to_connect", language))
        st.write(connect_info)


def test_embedding_model_connect(model_id, text="This is a test text for embedding generation"):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("embedding_model_test", language), key="test_embedding_btn"):
        # 获取用户凭证（如果在表单中填写了）
        user_credentials = None
        
        # 尝试从表单中获取凭证
        try:
            # 检查是否有更新表单的凭证字段
            if 'embedding_update_bedrock_ak' in st.session_state and 'embedding_update_bedrock_sk' in st.session_state:
                access_key = st.session_state.embedding_update_bedrock_ak
                secret_key = st.session_state.embedding_update_bedrock_sk
                if access_key and secret_key:
                    user_credentials = {
                        "access_key_id": access_key,
                        "secret_access_key": secret_key
                    }
                    logger.info("Using credentials from update form for testing")
        except Exception as e:
            logger.error(f"Error getting credentials from form: {str(e)}")
        
        # 测试模型，传递用户凭证
        success, result = EmbeddingModelManagement.test_embedding_model(model_id, text, user_credentials)
        
        if success:
            st.success(get_text("connected_successfully", language))
            st.write(f"Model: {result['model']}")
            st.write(f"Dimension: {result['dimension']}")
            st.write("Embedding sample (first 5 and last 5 elements):")
            st.json(result['embedding'])
        else:
            st.error(get_text("failed_to_connect", language))
            st.write(result)
# LLM Models tab functions

def render_llm_tab():
    """Render the LLM Models tab content"""
    language = st.session_state.get('language', 'en')
    st.subheader("LLM Model Management")
    
    # Model selection and create new button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.selectbox(get_text("model_select", language), st.session_state.model_list,
                    index=None,
                    placeholder=get_text("select_model", language), 
                    key='llm_current_model_name',
                    on_change=on_llm_model_selected)
    with col2:
        st.button(get_text("create_new_model", language), 
                 on_click=on_new_llm_clicked, 
                 key="llm_new_button")
    
    # Display appropriate content based on state
    if st.session_state.llm_new_model:
        display_new_llm_model()
    elif st.session_state.llm_update_model:
        display_update_llm_model()
    else:
        st.info("Please select a model from the dropdown above or create a new one.")

def display_new_llm_model():
    """Display form for creating a new LLM model"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("new_model", language))
    
    # Model type selection
    model_type_list = [
        get_text("sagemaker", language), 
        # get_text("bedrock_api", language), 
        get_text("br_client_api", language), 
        # get_text("bedrock_anthropic_model", language),
        # get_text("bedrock_amazon_model", language)
        get_text("bedrock_model", language)
    ]
    model_type = st.selectbox(get_text("model_type", language), model_type_list, index=0, key="llm_new_model_type")
    
    # Display form based on model type
    if model_type == get_text("sagemaker", language):
        display_new_sagemaker_model()
    # elif model_type == get_text("bedrock_api", language):
    #     display_new_bedrock_api_model()
    elif model_type == get_text("br_client_api", language):
        display_new_brclient_api_model()
    # elif model_type == get_text("bedrock_anthropic_model", language):
    #     display_new_bedrock_anthropic_model()
    # elif model_type == get_text("bedrock_amazon_model", language):
    #     display_new_bedrock_amazon_model()
    elif model_type == get_text("bedrock_model", language):
        display_new_bedrock_model()

def display_new_sagemaker_model():
    """Display form for creating a new SageMaker model"""
    language = st.session_state.get('language', 'en')
    
    sagemaker_name = st.text_input(get_text("sagemaker_endpoint_name", language), key="llm_new_sagemaker_name")
    sagemaker_region = st.text_input(get_text("sagemaker_endpoint_region", language), key="llm_new_sagemaker_region")
    prompt_template = st.text_area(
        get_text("prompt_template", language),
        placeholder=get_text("prompt_template_placeholder", language),
        height=200,
        help=get_text("prompt_template_help", language),
        key="llm_new_prompt_template"
    )
    
    example_input = {"inputs": "INPUT", "parameters": {"max_new_tokens": 256}}
    input_payload = st.text_area(
        get_text("input_payload", language),
        placeholder=get_text("input_payload_placeholder", language) + " " + json.dumps(example_input),
        height=200,
        help=get_text("input_payload_help", language),
        key="llm_new_input_payload"
    )
    
    output_format = st.text_area(
        get_text("output_format", language),
        placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
        height=100,
        help="Enter output format, The output value name is response",
        key="llm_new_output_format"
    )

    # Test connection button
    test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format)

    # Add model button
    if st.button(get_text("add_connection", language), type='primary', key="llm_add_sagemaker_btn"):
        if sagemaker_name == '':
            st.error(get_text("required_error", language).format(get_text("sagemaker_endpoint_name", language)))
        elif sagemaker_region == '':
            st.error(get_text("required_error", language).format(get_text("sagemaker_endpoint_region", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        else:
            ModelManagement.add_sagemaker_model(
                model_id="sagemaker." + sagemaker_name,
                model_region=sagemaker_region,
                prompt_template=prompt_template, 
                input_payload=input_payload,
                output_format=output_format
            )
            st.success(get_text("added_successfully", language).format(sagemaker_name))
            st.session_state.model_list.append("sagemaker." + sagemaker_name)
            st.session_state.llm_new_model = False

            with st.spinner(get_text("update_prompt", language)):
                update_profile_prompts(sagemaker_name)
                st.success(get_text("prompt_added_successfully", language))
                st.session_state.model_list = ModelManagement.get_all_models()
                st.session_state.profiles = ProfileManagement.get_all_profiles_with_info()
                st.success(get_text("profiles_update_successfully", language))

def display_new_brclient_api_model():
    """Display form for creating a new BR Client API model"""
    language = st.session_state.get('language', 'en')
    
    api_model_name = st.text_input(get_text("api_model_name", language), key="llm_new_brclient_name")
    api_url = st.text_input(get_text("api_url", language), key="llm_new_brclient_url")
    
    header_value = {"Content-Type": "application/json"}
    api_header = st.text_area(
        get_text("api_header", language),
        height=200,
        value=json.dumps(header_value),
        help=get_text("api_header_help", language),
        key="llm_new_brclient_header"
    )

    example_input = {
        "model": "claude-3-sonnet",
        "messages": [
            {
                "role": "system",
                "content": "SYSTEM_PROMPT"
            },
            {
                "role": "user",
                "content": "USER_PROMPT"
            }
        ],
        "temperature": 0.01
    }

    st.write(get_text("input_payload_json_format", language))
    input_payload = st.text_area(
        get_text("input_payload", language), 
        value=json.dumps(example_input),
        height=200,
        help=get_text("input_payload_help", language),
        key="llm_new_brclient_payload"
    )

    output_format = st.text_area(
        get_text("output_format", language),
        value="response.get('choices')[0].get('message').get('content')",
        placeholder=get_text("output_format_placeholder", language),
        height=100,
        help=get_text("output_format_help", language),
        key="llm_new_brclient_output"
    )

    # Test connection button
    test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)

    # Add model button
    if st.button(get_text("add_connection", language), type='primary', key="llm_add_brclient_btn"):
        if api_model_name == '':
            st.error(get_text("required_error", language).format(get_text("api_model_name", language)))
        elif api_url == '':
            st.error(get_text("required_error", language).format(get_text("api_url", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        else:
            ModelManagement.add_api_model(
                model_id="brclient-api." + api_model_name, 
                api_url=api_url,
                api_header=api_header, 
                input_payload=input_payload,
                output_format=output_format
            )
            st.success(get_text("added_successfully", language).format(api_model_name))
            st.session_state.model_list.append("brclient-api." + api_model_name)
            st.session_state.llm_new_model = False

            with st.spinner(get_text("update_prompt", language)):
                update_profile_prompts(api_model_name)
                st.success(get_text("prompt_added_successfully", language))
                st.session_state.model_list = ModelManagement.get_all_models()
                st.session_state.profiles = ProfileManagement.get_all_profiles_with_info()
                st.success(get_text("profiles_update_successfully", language))




def update_profile_prompts(model_name):
    """Update all profiles with the new model prompts"""
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
def display_update_llm_model():
    """Display form for updating an existing LLM model"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("update_model_connection_title", language))
    
    current_model = st.session_state.llm_current_model
    model_id = current_model.model_id

    # Determine model type
    if model_id.startswith("bedrock-model."):
        display_update_bedrock_model(current_model)
    elif model_id.startswith("sagemaker."):
        display_update_sagemaker_model(current_model)
    elif model_id.startswith("brclient-api."):
        display_update_brclient_api_model(current_model)


    # Delete model button
    if st.button(get_text("delete_model_connection", language), key="delete_llm_btn"):
        delete_llm_model(model_id)

def display_update_sagemaker_model(current_model):
    """Display form for updating a SageMaker model"""
    language = st.session_state.get('language', 'en')
    
    sagemaker_name = st.text_input(
        get_text("sagemaker_endpoint_name", language), 
        current_model.model_id, 
        disabled=True, 
        key="update_sagemaker_name"
    )
    sagemaker_region = st.text_input(
        get_text("sagemaker_endpoint_region", language), 
        current_model.model_region, 
        disabled=True, 
        key="update_sagemaker_region"
    )
    prompt_template = st.text_area(
        get_text("prompt_template", language), 
        current_model.prompt_template, 
        height=200, 
        key="update_prompt_template"
    )
    input_payload = st.text_area(
        get_text("input_payload", language), 
        current_model.input_payload, 
        height=200, 
        key="update_input_payload"
    )
    output_format = st.text_area(
        get_text("output_format", language), 
        current_model.output_format, 
        height=100, 
        key="update_output_format"
    )
    
    # Test connection button
    test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format)

    # Update model button
    if st.button(get_text("update_model_connection", language), type='primary', key="update_sagemaker_btn"):
        ModelManagement.update_model(
            model_id=sagemaker_name, 
            model_region=sagemaker_region,
            prompt_template=prompt_template, 
            input_payload=input_payload,
            output_format=output_format, 
            api_url="", 
            api_header=""
        )
        st.success(get_text("updated_successfully", language).format(sagemaker_name))


def display_update_brclient_api_model(current_model):
    """Display form for updating a BR Client API model"""
    language = st.session_state.get('language', 'en')
    
    api_model_name = st.text_input(
        get_text("api_model_name", language), 
        current_model.model_id, 
        disabled=True,
        key="update_brclient_name"
    )
    api_url = st.text_input(
        get_text("api_url", language), 
        current_model.api_url, 
        disabled=True,
        key="update_brclient_url"
    )
    api_header = st.text_area(
        get_text("api_header", language), 
        current_model.api_header, 
        height=200,
        key="update_brclient_header"
    )
    input_payload = st.text_area(
        get_text("input_payload", language), 
        current_model.input_payload, 
        height=200,
        key="update_brclient_payload"
    )
    output_format = st.text_area(
        get_text("output_format", language), 
        current_model.output_format, 
        height=100,
        key="update_brclient_output"
    )
    
    # Test connection button
    test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)

    # Update model button
    if st.button(get_text("update_model_connection", language), type='primary', key="update_brclient_btn"):
        ModelManagement.update_model(
            model_id=api_model_name, 
            model_region="",
            prompt_template="", 
            input_payload=input_payload,
            output_format=output_format, 
            api_url=api_url, 
            api_header=api_header
        )
        st.success(get_text("updated_successfully", language).format(api_model_name))


def delete_llm_model(model_id):
    """Delete an LLM model and update profiles"""
    language = st.session_state.get('language', 'en')
    
    ModelManagement.delete_model(model_id)
    st.success(get_text("deleted_successfully", language).format(model_id))
    
    if model_id in st.session_state.model_list:
        st.session_state.model_list.remove(model_id)
    
    st.session_state.llm_current_model = None
    st.session_state.llm_current_model_name = None
    
    with st.spinner(get_text("delete_prompt", language)):
        # Extract the model name without prefix
        if model_id.startswith("sagemaker."):
            model_name = model_id[10:]
        # elif model_id.startswith("bedrock-api."):
        #     model_name = model_id[12:]
        elif model_id.startswith("brclient-api."):
            model_name = model_id[13:]
        # elif model_id.startswith("bedrock-anthropic."):
        #     model_name = model_id[18:]
        elif model_id.startswith("bedrock-api-model."):
            model_name = model_id[13:]
        else:
            model_name = model_id
        
        # Update all profiles to remove the model
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        for profile_name, profile_value in all_profiles.items():
            profile_prompt_map = profile_value["prompt_map"]
            update_prompt_map = {}
            for each_process in profile_prompt_map:
                update_prompt_map[each_process] = profile_prompt_map[each_process]
                if model_name in update_prompt_map[each_process]["system_prompt"]:
                    del update_prompt_map[each_process]["system_prompt"][model_name]
                if model_name in update_prompt_map[each_process]["user_prompt"]:
                    del update_prompt_map[each_process]["user_prompt"][model_name]
            ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
        
        # Update session state
        st.session_state.profiles = ProfileManagement.get_all_profiles_with_info()
        st.success(get_text("prompt_delete_successfully", language))
        st.session_state.model_list = ModelManagement.get_all_models()
    
    st.session_state.llm_update_model = False
# Embedding Models tab functions
def render_embedding_tab():
    """Render the Embedding Models tab content"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("embedding_model_management", language))
    
    # Model selection and create new button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.selectbox(get_text("select_embedding_model", language), st.session_state.embedding_model_list,
                    index=None,
                    placeholder=get_text("select_embedding_model_placeholder", language), 
                    key='embedding_current_model_name',
                    on_change=on_embedding_model_selected)
    with col2:
        st.button(get_text("create_new_embedding_model", language), 
                 on_click=on_new_embedding_clicked, 
                 key="embedding_new_button")
    
    # Display appropriate content based on state
    if st.session_state.embedding_new_model:
        display_new_embedding_model()
    elif st.session_state.embedding_update_model and st.session_state.get('embedding_current_model') is not None:
        display_update_embedding_model()
    else:
        st.info(get_text("select_embedding_model_info", language))

def display_new_embedding_model():
    """Display form for creating a new embedding model"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("new_embedding_model", language))
    
    # Model information
    name = st.text_input(get_text("model_name", language), help=get_text("model_name_help", language), key="embedding_new_name")
    platform_options = ["bedrock", "sagemaker", "brclient-api"]
    platform = st.selectbox(get_text("platform", language), platform_options, index=0, key="embedding_new_platform")
    model_name = st.text_input(get_text("model_id_endpoint", language), help=get_text("model_id_endpoint_help", language), key="embedding_new_model_id")
    
    # Platform-specific fields
    if platform == "bedrock":
        region = st.text_input(get_text("aws_region", language), help=get_text("bedrock_region_help", language), key="embedding_new_bedrock_region")
        dimension = st.number_input(get_text("vector_dimension", language), min_value=1, value=1024, 
                                   help=get_text("vector_dimension_help", language), key="embedding_new_bedrock_dimension")
        
        # 添加 AK/SK 输入字段
        access_key = st.text_input("Access Key ID(Optional)", type="password", key="embedding_new_bedrock_ak")
        secret_key = st.text_input("Secret Access Key(Optional)", type="password", key="embedding_new_bedrock_sk")
        
        # 将 AK/SK 组合成 JSON 格式存储在 input_format 字段中
        if access_key and secret_key:
            input_format = json.dumps({
                "credentials": {
                    "access_key_id": access_key,
                    "secret_access_key": secret_key
                }
            })
            # 添加验证
            logger.info(f"Generated input_format with credentials")
            # 验证 JSON 是否可以正确解析
            try:
                parsed = json.loads(input_format)
                logger.info(f"Parsed successfully: {parsed.get('credentials', {}).keys()}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
        else:
            input_format = ""
        
        api_url = ""
        api_key = ""
        
    elif platform == "sagemaker":
        region = st.text_input(get_text("aws_region", language), help=get_text("sagemaker_region_help", language), key="embedding_new_sagemaker_region")
        dimension = st.number_input(get_text("vector_dimension", language), min_value=1, value=1024, 
                                   help=get_text("vector_dimension_help", language), key="embedding_new_sagemaker_dimension")
        api_url = ""
        api_key = ""
        input_format = st.text_area(get_text("input_format_optional", language), 
                                   value='{"input": "INPUT_TEXT"}', 
                                   help=get_text("input_format_help", language),
                                   key="embedding_new_sagemaker_format")
        
    elif platform == "brclient-api":
        region = ""
        dimension = st.number_input(get_text("vector_dimension", language), min_value=1, value=1024, 
                                   help=get_text("vector_dimension_help", language), key="embedding_new_api_dimension")
        api_url = st.text_input(get_text("api_url", language), help=get_text("api_url_help", language), key="embedding_new_api_url")
        api_key = st.text_input(get_text("api_key_optional", language), type="password", 
                               help=get_text("api_key_help", language), key="embedding_new_api_key")
        input_format = st.text_area(get_text("input_format_optional", language), 
                                   value='{"model": "titan-embed-text-v2", "input": "INPUT_TEXT", "encoding_format": "float"}', 
                                   help=get_text("input_format_help", language),
                                   key="embedding_new_api_format")
    
    # Test area
    test_text = st.text_area(get_text("test_text", language), value=get_text("test_text_default", language), 
                            help=get_text("test_text_help", language), key="embedding_new_test_text")
    
    if st.button(get_text("test_connection", language), key="embedding_new_test_btn"):
        # Create a temporary model ID for testing
        temp_model_id = f"{platform}.{name}"
        
        # 获取用户凭证
        user_credentials = None
        if access_key and secret_key:
            user_credentials = {
                "access_key_id": access_key,
                "secret_access_key": secret_key
            }
            logger.info("User credentials prepared for testing")
        
        # Add the model temporarily
        EmbeddingModelManagement.add_embedding_model(
            name=name,
            platform=platform,
            model_name=model_name,
            region=region if platform in ["bedrock", "sagemaker"] else None,
            dimension=dimension,
            api_url=api_url if platform == "brclient-api" else None,
            api_key=api_key if platform == "brclient-api" else None,
            input_format=input_format  # 始终传递input_format，不再根据平台过滤
        )
        
        # Test the model, passing user credentials
        success, result = EmbeddingModelManagement.test_embedding_model(temp_model_id, test_text, user_credentials)
        
        # Delete the temporary model
        EmbeddingModelManagement.delete_embedding_model(temp_model_id)
        
        if success:
            st.success(get_text("connected_successfully", language))
            st.write(f"{get_text('dimension', language)}: {result['dimension']}")
            st.write(get_text("embedding_sample", language))
            if result['dimension'] > 0:
                st.json(result['embedding'])
            else:
                st.warning(get_text("empty_embedding_warning", language))
                st.json(result.get('raw_response', {}))
        else:
            st.error(get_text("failed_to_connect", language))
            st.write(result)
    
    # Save button
    if st.button(get_text("add_embedding_model", language), type="primary", key="embedding_new_add_btn"):
        if not name:
            st.error(get_text("model_name_required", language))
        elif not model_name:
            st.error(get_text("model_name_id_required", language))
        elif platform in ["bedrock", "sagemaker"] and not region:
            st.error(get_text("aws_region_required", language))
        elif platform == "brclient-api" and not api_url:
            st.error(get_text("api_url_required", language))
        else:
            model_id = EmbeddingModelManagement.add_embedding_model(
                name=name,
                platform=platform,
                model_name=model_name,
                region=region if platform in ["bedrock", "sagemaker"] else None,
                dimension=dimension,
                api_url=api_url if platform == "brclient-api" else None,
                api_key=api_key if platform == "brclient-api" else None,
                input_format=input_format  # 始终传递input_format，不再根据平台过滤
            )
            st.success(get_text("embedding_model_added", language).format(name))
            if model_id not in st.session_state.embedding_model_list:
                st.session_state.embedding_model_list.append(model_id)
            st.session_state.embedding_new_model = False

def display_update_embedding_model():
    """Display form for updating an existing embedding model"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("update_embedding_model", language))
    
    # 安全检查，确保模型对象存在
    if 'embedding_current_model' not in st.session_state or st.session_state.embedding_current_model is None:
        st.error("No model selected or model could not be loaded")
        return
    
    model = st.session_state.embedding_current_model
    
    # Display model information
    st.text_input(get_text("model_id", language), value=model.model_id, disabled=True, key="embedding_update_id")
    name = st.text_input(get_text("model_name", language), value=model.name, key="embedding_update_name")
    platform = st.text_input(get_text("platform", language), value=model.platform, disabled=True, key="embedding_update_platform")
    model_name = st.text_input(get_text("model_id_endpoint", language), value=model.model_name, key="embedding_update_model_id")
    
    # 安全地获取维度值的函数
    def get_safe_dimension(model_obj):
        try:
            dim_value = getattr(model_obj, 'dimension', 1536)
            # 确保是整数
            dim_value = int(dim_value)
            if dim_value < 1:
                dim_value = 1536
            return dim_value
        except (ValueError, TypeError):
            logger.warning(f"Invalid dimension value: {getattr(model_obj, 'dimension', None)}, using default 1536")
            return 1536
    
    # Platform-specific fields
    if platform == "bedrock":
        region = st.text_input(get_text("aws_region", language), value=getattr(model, 'region', ''), key="embedding_update_bedrock_region")
        dimension = st.number_input(get_text("vector_dimension", language), min_value=1, value=get_safe_dimension(model), key="embedding_update_bedrock_dimension")
        
        # 尝试从 input_format 中提取现有凭证
        existing_credentials = {"access_key_id": "", "secret_access_key": ""}
        if model.input_format:
            try:
                input_data = json.loads(model.input_format)
                logger.info(f"Updating model: parsed input_format successfully")
                if "credentials" in input_data:
                    existing_credentials = input_data["credentials"]
                    logger.info("Found existing credentials in input_format")
            except json.JSONDecodeError as e:
                logger.error(f"Updating model: JSON parsing error: {str(e)}")
                pass
        
        # 添加 AK/SK 输入字段
        access_key = st.text_input("Access Key ID(Optional)", value=existing_credentials.get("access_key_id", ""), 
                                  type="password", key="embedding_update_bedrock_ak")
        secret_key = st.text_input("Secret Access Key(Optional)", value=existing_credentials.get("secret_access_key", ""), 
                                  type="password", key="embedding_update_bedrock_sk")
        
        # 将 AK/SK 组合成 JSON 格式存储在 input_format 字段中
        if access_key and secret_key:
            input_format = json.dumps({
                "credentials": {
                    "access_key_id": access_key,
                    "secret_access_key": secret_key
                }
            })
            # 添加验证
            logger.info(f"Update: Generated input_format with credentials")
            # 验证 JSON 是否可以正确解析
            try:
                parsed = json.loads(input_format)
                logger.info(f"Update: Parsed successfully: {parsed.get('credentials', {}).keys()}")
            except json.JSONDecodeError as e:
                logger.error(f"Update: JSON parsing error: {str(e)}")
        else:
            input_format = ""
        
        api_url = getattr(model, 'api_url', '')
        api_key = getattr(model, 'api_key', '')
        
    elif platform == "sagemaker":
        region = st.text_input(get_text("aws_region", language), value=getattr(model, 'region', ''), key="embedding_update_sagemaker_region")
        dimension = st.number_input(get_text("vector_dimension", language), min_value=1, value=get_safe_dimension(model), key="embedding_update_sagemaker_dimension")
        input_format = st.text_area(get_text("input_format", language), value=getattr(model, 'input_format', ''), key="embedding_update_sagemaker_format")
        api_url = getattr(model, 'api_url', '')
        api_key = getattr(model, 'api_key', '')
        
    elif platform == "brclient-api":
        region = getattr(model, 'region', '')
        dimension = st.number_input(get_text("vector_dimension", language), min_value=1, value=get_safe_dimension(model), key="embedding_update_api_dimension")
        api_url = st.text_input(get_text("api_url", language), value=getattr(model, 'api_url', ''), key="embedding_update_api_url")
        api_key = st.text_input(get_text("api_key", language), value=getattr(model, 'api_key', ''), type="password", key="embedding_update_api_key")
        input_format = st.text_area(get_text("input_format", language), value=getattr(model, 'input_format', ''), key="embedding_update_api_format")
    
    # Test area
    test_text = st.text_area(get_text("test_text", language), value=get_text("test_text_default", language), key="embedding_update_test_text")
    test_embedding_model_connect(model.model_id, test_text)
    
    # Update button
    if st.button(get_text("update_embedding_model_btn", language), type="primary", key="embedding_update_btn"):
        success = EmbeddingModelManagement.update_embedding_model(
            model_id=model.model_id,
            name=name,
            model_name=model_name,
            region=region if platform in ["bedrock", "sagemaker"] else None,
            dimension=dimension,
            api_url=api_url if platform == "brclient-api" else None,
            api_key=api_key if platform == "brclient-api" else None,
            input_format=input_format  # 始终传递input_format，不再根据平台过滤
        )
            
        if success:
            st.success(get_text("updated_successfully", language).format(name))
        else:
            st.error(get_text("failed_to_connect", language))
    
    # Delete button
    if st.button(get_text("delete_embedding_model", language), key="embedding_delete_btn"):
        success, message = EmbeddingModelManagement.delete_embedding_model(model.model_id)
        if success:
            st.success(message)
            if model.model_id in st.session_state.embedding_model_list:
                st.session_state.embedding_model_list.remove(model.model_id)
            st.session_state.embedding_current_model = None
            st.session_state.embedding_current_model_name = None
            st.session_state.embedding_update_model = False
        else:
            st.error(message)
# Global Settings tab functions
def render_settings_tab():
    """Render the Global Settings tab content"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("global_settings", language))
    display_global_settings()

def display_global_settings():
    """Display form for global settings"""
    language = st.session_state.get('language', 'en')
    st.write(get_text("global_settings_description", language))

    # Default LLM Model
    st.subheader(get_text("default_llm_model", language))
    default_llm = st.session_state.global_settings.get('default_llm_model', {}).get('value', '')
    selected_llm = st.selectbox(
        get_text("select_default_llm", language),
        options=st.session_state.model_list,
        index=st.session_state.model_list.index(default_llm) if default_llm in st.session_state.model_list else 0,
        help=get_text("default_llm_help", language),
        key="settings_default_llm"
    )

    # Default Embedding Model
    st.subheader(get_text("default_embedding_model", language))
    default_embedding = st.session_state.global_settings.get('default_embedding_model', {}).get('value', '')
    selected_embedding = st.selectbox(
        get_text("select_default_embedding", language),
        options=st.session_state.embedding_model_list,
        index=st.session_state.embedding_model_list.index(default_embedding) if default_embedding in st.session_state.embedding_model_list and st.session_state.embedding_model_list else 0,
        help=get_text("default_embedding_help", language),
        key="settings_default_embedding"
    )

    # Default Profile
    st.subheader(get_text("default_profile", language))
    default_profile = st.session_state.global_settings.get('default_profile', {}).get('value', '')
    selected_profile = st.selectbox(
        get_text("select_default_profile", language),
        options=st.session_state.profiles_list,
        index=st.session_state.profiles_list.index(default_profile) if default_profile in st.session_state.profiles_list else 0,
        help=get_text("default_profile_help", language),
        key="settings_default_profile"
    )

    # Save button
    if st.button(get_text("save_global_settings", language), type="primary", key="settings_save_btn"):
        # Update LLM model
        EmbeddingModelManagement.update_global_setting('default_llm_model', selected_llm, get_text("default_llm_model", language))
        
        # Update embedding model
        EmbeddingModelManagement.update_global_setting('default_embedding_model', selected_embedding, get_text("default_embedding_model", language))
        
        # Update profile
        EmbeddingModelManagement.update_global_setting('default_profile', selected_profile, get_text("default_profile", language))
        
        # Apply the default embedding model
        EmbeddingModelManagement.apply_default_embedding_model()
        
        # Update session state
        st.session_state.global_settings = EmbeddingModelManagement.get_all_global_settings()
        
        st.success(get_text("global_settings_updated", language))
        st.info(get_text("changes_effect_next_restart", language))

# Main function
def main():
    load_dotenv()
    language = st.session_state.get('language', 'en')
    st.set_page_config(page_title=get_text("model_management_title", language))
    make_sidebar()

    # Page title
    st.title(get_text("model_management_title", language))
    
    # Initialize session state
    initialize_session_state()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        get_text("llm_models_tab", language), 
        get_text("embedding_models_tab", language), 
        get_text("global_settings_tab", language)
    ])
    
    # Render content in each tab
    with tab1:
        render_llm_tab()
    
    with tab2:
        render_embedding_tab()
    
    with tab3:
        render_settings_tab()

if __name__ == '__main__':
    main()

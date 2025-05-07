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
# Connection test functions - Unified approach
def test_model_connection(model_type, params, test_btn_key):
    """Generic function to test model connections
    
    Args:
        model_type: Type of model (sagemaker, api, bedrock_anthropic, etc.)
        params: Dictionary of parameters needed for the connection
        test_btn_key: Unique key for the test button
    """
    language = st.session_state.get('language', 'en')
    
    if st.button(get_text("model_connection_test", language), key=test_btn_key):
        # Validate required parameters
        missing_params = []
        for param_name, param_value in params.items():
            if param_value == '' and param_name != 'prompt_template':  # prompt_template can be empty
                missing_params.append(param_name)
        
        if missing_params:
            for param in missing_params:
                st.error(get_text("required_error", language).format(get_text(param, language)))
            return
        
        # Call appropriate test function based on model type
        connect_flag = False
        connect_info = "-1"
        
        try:
            if model_type == "sagemaker":
                # Implementation for SageMaker model connection test
                connect_flag = True
                connect_info = "SageMaker connection successful"
            elif model_type == "bedrock_api":
                connect_flag, connect_info = test_bedrock_api(**params)
            elif model_type == "brclient_api":
                connect_flag, connect_info = test_brclient_api(**params)
            elif model_type == "bedrock_anthropic":
                connect_flag, connect_info = test_bedrock_anthropic(**params)
            elif model_type == "bedrock_amazon":
                connect_flag, connect_info = test_bedrock_amazon(**params)
            elif model_type == "embedding":
                connect_flag, connect_info = test_embedding(**params)
            
            # Display results
            if connect_flag:
                st.success(get_text("connected_successfully", language))
            else:
                st.error(get_text("failed_to_connect", language))
            
            st.write(connect_info)
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            st.error(f"Error: {str(e)}")

def test_bedrock_api(api_model_name, api_url, api_header, input_payload, output_format, **kwargs):
    """Test connection to Bedrock API"""
    try:
        if api_model_name.startswith("bedrock-api."):
            api_model_name = api_model_name[12:]
        header = json.loads(api_header)
        input_payload = json.loads(input_payload)
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        input_payload["system"] = system_prompt
        input_payload["messages"][0]["content"] = user_prompt
        input_payload["model_id"] = api_model_name
        response = requests.post(api_url, headers=header, data=json.dumps(input_payload))
        response = response.json()
        answer = eval(output_format)
        return True, answer
    except Exception as e:
        logger.error(f"Failed to connect to Bedrock API: {e}")
        return False, str(e)

def test_brclient_api(api_model_name, api_url, api_header, input_payload, output_format, **kwargs):
    """Test connection to BR Client API"""
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
        return True, answer
    except Exception as e:
        logger.error(f"Failed to connect to BR Client API: {e}")
        return False, str(e)

def test_bedrock_anthropic(bedrock_model_name_id, bedrock_region, input_payload, output_format, **kwargs):
    """Test connection to Bedrock Anthropic model"""
    try:
        config = Config(region_name=bedrock_region, signature_version='v4',
                        retries={
                            'max_attempts': 10,
                            'mode': 'standard'
                        }, read_timeout=600)
        bedrock = boto3.client(service_name='bedrock-runtime', config=config)

        input_payload = json.loads(input_payload)

        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        input_payload["system"] = system_prompt
        input_payload["messages"][0]["content"] = user_prompt
        body = json.dumps(input_payload)
        response_info = bedrock.invoke_model(body=body, modelId=bedrock_model_name_id)
        response = json.loads(response_info.get('body').read())
        answer = eval(output_format)
        return True, answer
    except Exception as e:
        logger.error(f"Failed to connect to Bedrock Anthropic: {e}")
        return False, str(e)

def test_bedrock_amazon(amazon_model_name, bedrock_region, input_payload, output_format, **kwargs):
    """Test connection to Bedrock Amazon model"""
    try:
        config = Config(region_name=bedrock_region, signature_version='v4',
                        retries={
                            'max_attempts': 10,
                            'mode': 'standard'
                        }, read_timeout=600)
        bedrock = boto3.client(service_name='bedrock-runtime', config=config)

        input_payload = json.loads(input_payload)
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        input_payload["system"][0]["text"] = system_prompt
        input_payload["messages"][0]["content"][0]["text"] = user_prompt
        body = json.dumps(input_payload)
        response_info = bedrock.invoke_model(body=body, modelId=amazon_model_name)
        response = json.loads(response_info.get('body').read())
        answer = eval(output_format)
        return True, answer
    except Exception as e:
        logger.error(f"Failed to connect to Bedrock Amazon: {e}")
        return False, str(e)

def test_embedding(model_id, text="This is a test text for embedding generation", **kwargs):
    """Test connection to embedding model"""
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
        return True, {
            "model": result['model'],
            "dimension": result['dimension'],
            "embedding": result['embedding']
        }
    else:
        return False, result
# Helper functions for updating profile prompts
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

# Form validation helper
def validate_form_fields(required_fields, language):
    """Validate that all required fields are filled
    
    Args:
        required_fields: Dictionary of field names and their values
        language: Current language for error messages
        
    Returns:
        bool: True if all fields are valid, False otherwise
    """
    valid = True
    for field_name, field_value in required_fields.items():
        if field_value == '':
            st.error(get_text("required_error", language).format(get_text(field_name, language)))
            valid = False
    return valid

# Generic model form display
def display_model_form(form_type, model_type, fields, test_params=None, submit_action=None, test_btn_key=None):
    """Display a generic model form
    
    Args:
        form_type: 'new' or 'update'
        model_type: Type of model (sagemaker, api, etc.)
        fields: Dictionary of field configurations
        test_params: Parameters for testing the connection
        submit_action: Function to call on form submission
        test_btn_key: Key for the test button
    """
    language = st.session_state.get('language', 'en')
    
    # Display form fields
    field_values = {}
    for field_name, field_config in fields.items():
        field_type = field_config.get('type', 'text_input')
        field_key = f"{form_type}_{model_type}_{field_name}"
        
        if field_type == 'text_input':
            field_values[field_name] = st.text_input(
                get_text(field_config.get('label', field_name), language),
                value=field_config.get('value', ''),
                disabled=field_config.get('disabled', False),
                type=field_config.get('input_type', 'default'),
                key=field_key
            )
        elif field_type == 'text_area':
            field_values[field_name] = st.text_area(
                get_text(field_config.get('label', field_name), language),
                value=field_config.get('value', ''),
                height=field_config.get('height', 200),
                disabled=field_config.get('disabled', False),
                key=field_key
            )
        elif field_type == 'number_input':
            field_values[field_name] = st.number_input(
                get_text(field_config.get('label', field_name), language),
                min_value=field_config.get('min_value', 0),
                value=field_config.get('value', 0),
                disabled=field_config.get('disabled', False),
                key=field_key
            )
    
    # Test connection if parameters are provided
    if test_params:
        # Update test parameters with form values
        for param, value in field_values.items():
            if param in test_params:
                test_params[param] = value
        
        # Display test button
        test_model_connection(model_type, test_params, test_btn_key or f"{form_type}_{model_type}_test_btn")
    
    # Submit button
    if submit_action and st.button(
        get_text(f"{form_type}_connection", language), 
        type='primary', 
        key=f"{form_type}_{model_type}_submit_btn"
    ):
        # Validate required fields
        required_fields = {k: v for k, v in field_values.items() 
                          if fields[k].get('required', False)}
        
        if validate_form_fields(required_fields, language):
            # Call submit action with form values
            result = submit_action(**field_values)
            
            if result.get('success', False):
                st.success(get_text(f"{form_type}d_successfully", language).format(result.get('name', '')))
                
                # Additional actions after successful submission
                if result.get('update_profiles', False):
                    with st.spinner(get_text("update_prompt", language)):
                        update_profile_prompts(result.get('model_name', ''))
                        st.success(get_text("prompt_added_successfully", language))
                        st.session_state.model_list = ModelManagement.get_all_models()
                        st.session_state.profiles = ProfileManagement.get_all_profiles_with_info()
                        st.success(get_text("profiles_update_successfully", language))
                
                # Reset form state if needed
                if form_type == 'new':
                    if 'llm' in model_type:
                        st.session_state.llm_new_model = False
                    elif 'embedding' in model_type:
                        st.session_state.embedding_new_model = False
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
        get_text("bedrock_api", language), 
        get_text("br_client_api", language), 
        get_text("bedrock_anthropic_model", language),
        get_text("bedrock_amazon_model", language)
    ]
    model_type = st.selectbox(get_text("model_type", language), model_type_list, index=0, key="llm_new_model_type")
    
    # Display form based on model type
    if model_type == get_text("sagemaker", language):
        display_new_sagemaker_model()
    elif model_type == get_text("bedrock_api", language):
        display_new_bedrock_api_model()
    elif model_type == get_text("br_client_api", language):
        display_new_brclient_api_model()
    elif model_type == get_text("bedrock_anthropic_model", language):
        display_new_bedrock_anthropic_model()
    elif model_type == get_text("bedrock_amazon_model", language):
        display_new_bedrock_amazon_model()

def display_new_sagemaker_model():
    """Display form for creating a new SageMaker model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    fields = {
        'sagemaker_name': {
            'label': 'sagemaker_endpoint_name',
            'type': 'text_input',
            'required': True
        },
        'sagemaker_region': {
            'label': 'sagemaker_endpoint_region',
            'type': 'text_input',
            'required': True
        },
        'prompt_template': {
            'label': 'prompt_template',
            'type': 'text_area',
            'height': 200,
            'required': False
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps({"inputs": "INPUT", "parameters": {"max_new_tokens": 256}}),
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'sagemaker_name': '',
        'sagemaker_region': '',
        'prompt_template': '',
        'input_payload': '',
        'output_format': ''
    }
    
    # Submit action
    def submit_action(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format, **kwargs):
        model_id = "sagemaker." + sagemaker_name
        ModelManagement.add_sagemaker_model(
            model_id=model_id,
            model_region=sagemaker_region,
            prompt_template=prompt_template, 
            input_payload=input_payload,
            output_format=output_format
        )
        return {
            'success': True,
            'name': sagemaker_name,
            'model_name': sagemaker_name,
            'update_profiles': True
        }
    
    # Display form
    display_model_form(
        form_type='add',
        model_type='sagemaker',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="test_sagemaker_btn"
    )

def display_new_bedrock_api_model():
    """Display form for creating a new Bedrock API model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    header_value = {"Content-Type": "application/json"}
    messages = {"role": "user", "content": "USER_PROMPT"}
    example_input = {
        "anthropic_version": "bedrock-2023-05-31", 
        "max_tokens": 2024, 
        "system": "SYSTEM_PROMPT",
        "messages": [messages], 
        "temperature": 0.01
    }
    
    fields = {
        'api_model_name': {
            'label': 'api_model_name',
            'type': 'text_input',
            'required': True
        },
        'api_url': {
            'label': 'api_url',
            'type': 'text_input',
            'required': True
        },
        'api_header': {
            'label': 'api_header',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps(header_value),
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps(example_input),
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': "response.get('content')[0].get('text')",
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'api_model_name': '',
        'api_url': '',
        'api_header': '',
        'input_payload': '',
        'output_format': ''
    }
    
    # Submit action
    def submit_action(api_model_name, api_url, api_header, input_payload, output_format, **kwargs):
        model_id = "bedrock-api." + api_model_name
        ModelManagement.add_api_model(
            model_id=model_id, 
            api_url=api_url,
            api_header=api_header, 
            input_payload=input_payload,
            output_format=output_format
        )
        return {
            'success': True,
            'name': api_model_name,
            'model_name': api_model_name,
            'update_profiles': True
        }
    
    # Display form
    st.write("The Input Payload is Json format str, Parameters can be modified, but do not change the format")
    display_model_form(
        form_type='add',
        model_type='bedrock_api',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="test_bedrock_api_btn"
    )
def display_new_brclient_api_model():
    """Display form for creating a new BR Client API model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    header_value = {"Content-Type": "application/json"}
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
    
    fields = {
        'api_model_name': {
            'label': 'api_model_name',
            'type': 'text_input',
            'required': True
        },
        'api_url': {
            'label': 'api_url',
            'type': 'text_input',
            'required': True
        },
        'api_header': {
            'label': 'api_header',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps(header_value),
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps(example_input),
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': "response.get('choices')[0].get('message').get('content')",
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'api_model_name': '',
        'api_url': '',
        'api_header': '',
        'input_payload': '',
        'output_format': ''
    }
    
    # Submit action
    def submit_action(api_model_name, api_url, api_header, input_payload, output_format, **kwargs):
        model_id = "brclient-api." + api_model_name
        ModelManagement.add_api_model(
            model_id=model_id, 
            api_url=api_url,
            api_header=api_header, 
            input_payload=input_payload,
            output_format=output_format
        )
        return {
            'success': True,
            'name': api_model_name,
            'model_name': api_model_name,
            'update_profiles': True
        }
    
    # Display form
    st.write(get_text("input_payload_json_format", language))
    display_model_form(
        form_type='add',
        model_type='brclient_api',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="test_brclient_api_btn"
    )

def display_new_bedrock_anthropic_model():
    """Display form for creating a new Bedrock Anthropic model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    user_message = {"role": "user", "content": "USER_PROMPT"}
    messages = [user_message]
    example_input = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "system": "SYSTEM_PROMPT",
        "messages": messages,
        "temperature": 0.01
    }
    
    fields = {
        'bedrock_model_name': {
            'label': 'bedrock_anthropic_model_id',
            'type': 'text_input',
            'required': True
        },
        'bedrock_region': {
            'label': 'bedrock_anthropic_model_region',
            'type': 'text_input',
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps(example_input),
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': "response.get('content')[0].get('text')",
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'bedrock_model_name_id': '',
        'bedrock_region': '',
        'input_payload': '',
        'output_format': ''
    }
    
    # Submit action
    def submit_action(bedrock_model_name, bedrock_region, input_payload, output_format, **kwargs):
        model_id = "bedrock-anthropic." + bedrock_model_name
        ModelManagement.add_bedrock_anthropic_model(
            model_id=model_id,
            model_region=bedrock_region
        )
        return {
            'success': True,
            'name': bedrock_model_name,
            'model_name': bedrock_model_name,
            'update_profiles': True
        }
    
    # Display form
    display_model_form(
        form_type='add',
        model_type='bedrock_anthropic',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="test_bedrock_anthropic_btn"
    )

def display_new_bedrock_amazon_model():
    """Display form for creating a new Bedrock Amazon model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    system_list = [{"text": "SYSTEM_PROMPT"}]
    message_list = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
    inf_params = {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.01}
    example_input = {
        "schemaVersion": "messages-v1",
        "messages": message_list,
        "system": system_list,
        "inferenceConfig": inf_params,
    }
    
    fields = {
        'amazon_model_name': {
            'label': 'bedrock_amazon_nova_model_id',
            'type': 'text_input',
            'required': True
        },
        'bedrock_region': {
            'label': 'bedrock_amazon_nova_model_region',
            'type': 'text_input',
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': json.dumps(example_input),
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': "response['output']['message']['content'][0]['text']",
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'amazon_model_name': '',
        'bedrock_region': '',
        'input_payload': '',
        'output_format': ''
    }
    
    # Submit action
    def submit_action(amazon_model_name, bedrock_region, input_payload, output_format, **kwargs):
        model_id = "bedrock-nova." + amazon_model_name
        ModelManagement.add_bedrock_nova_model(
            model_id=model_id,
            model_region=bedrock_region, 
            input_payload=input_payload,
            output_format=output_format
        )
        return {
            'success': True,
            'name': amazon_model_name,
            'model_name': amazon_model_name,
            'update_profiles': True
        }
    
    # Display form
    display_model_form(
        form_type='add',
        model_type='bedrock_amazon',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="test_bedrock_amazon_btn"
    )
def display_update_llm_model():
    """Display form for updating an existing LLM model"""
    language = st.session_state.get('language', 'en')
    st.subheader(get_text("update_model_connection_title", language))
    
    current_model = st.session_state.llm_current_model
    model_id = current_model.model_id
    
    # Determine model type
    if model_id.startswith("bedrock-api."):
        display_update_bedrock_api_model(current_model)
    elif model_id.startswith("sagemaker."):
        display_update_sagemaker_model(current_model)
    elif model_id.startswith("brclient-api."):
        display_update_brclient_api_model(current_model)
    elif model_id.startswith("bedrock-anthropic."):
        display_update_bedrock_anthropic_model(current_model)
    elif model_id.startswith("bedrock-nova."):
        display_update_bedrock_amazon_model(current_model)
    
    # Delete model button
    if st.button(get_text("delete_model_connection", language), key="delete_llm_btn"):
        delete_llm_model(model_id)

def display_update_sagemaker_model(current_model):
    """Display form for updating a SageMaker model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    fields = {
        'sagemaker_name': {
            'label': 'sagemaker_endpoint_name',
            'type': 'text_input',
            'value': current_model.model_id,
            'disabled': True,
            'required': True
        },
        'sagemaker_region': {
            'label': 'sagemaker_endpoint_region',
            'type': 'text_input',
            'value': current_model.model_region,
            'disabled': True,
            'required': True
        },
        'prompt_template': {
            'label': 'prompt_template',
            'type': 'text_area',
            'height': 200,
            'value': current_model.prompt_template,
            'required': False
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': current_model.input_payload,
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': current_model.output_format,
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'sagemaker_name': current_model.model_id,
        'sagemaker_region': current_model.model_region,
        'prompt_template': current_model.prompt_template,
        'input_payload': current_model.input_payload,
        'output_format': current_model.output_format
    }
    
    # Submit action
    def submit_action(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format, **kwargs):
        ModelManagement.update_model(
            model_id=sagemaker_name, 
            model_region=sagemaker_region,
            prompt_template=prompt_template, 
            input_payload=input_payload,
            output_format=output_format, 
            api_url="", 
            api_header=""
        )
        return {
            'success': True,
            'name': sagemaker_name
        }
    
    # Display form
    display_model_form(
        form_type='update',
        model_type='sagemaker',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="update_sagemaker_test_btn"
    )

def display_update_bedrock_api_model(current_model):
    """Display form for updating a Bedrock API model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    fields = {
        'api_model_name': {
            'label': 'api_model_name',
            'type': 'text_input',
            'value': current_model.model_id,
            'disabled': True,
            'required': True
        },
        'api_url': {
            'label': 'api_url',
            'type': 'text_input',
            'value': current_model.api_url,
            'disabled': True,
            'required': True
        },
        'api_header': {
            'label': 'api_header',
            'type': 'text_area',
            'height': 200,
            'value': current_model.api_header,
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': current_model.input_payload,
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': current_model.output_format,
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'api_model_name': current_model.model_id,
        'api_url': current_model.api_url,
        'api_header': current_model.api_header,
        'input_payload': current_model.input_payload,
        'output_format': current_model.output_format
    }
    
    # Submit action
    def submit_action(api_model_name, api_url, api_header, input_payload, output_format, **kwargs):
        ModelManagement.update_model(
            model_id=api_model_name, 
            model_region="",
            prompt_template="", 
            input_payload=input_payload,
            output_format=output_format, 
            api_url=api_url, 
            api_header=api_header
        )
        return {
            'success': True,
            'name': api_model_name
        }
    
    # Display form
    display_model_form(
        form_type='update',
        model_type='bedrock_api',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="update_bedrock_api_test_btn"
    )
def display_update_brclient_api_model(current_model):
    """Display form for updating a BR Client API model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    fields = {
        'api_model_name': {
            'label': 'api_model_name',
            'type': 'text_input',
            'value': current_model.model_id,
            'disabled': True,
            'required': True
        },
        'api_url': {
            'label': 'api_url',
            'type': 'text_input',
            'value': current_model.api_url,
            'disabled': True,
            'required': True
        },
        'api_header': {
            'label': 'api_header',
            'type': 'text_area',
            'height': 200,
            'value': current_model.api_header,
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': current_model.input_payload,
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': current_model.output_format,
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'api_model_name': current_model.model_id,
        'api_url': current_model.api_url,
        'api_header': current_model.api_header,
        'input_payload': current_model.input_payload,
        'output_format': current_model.output_format
    }
    
    # Submit action
    def submit_action(api_model_name, api_url, api_header, input_payload, output_format, **kwargs):
        ModelManagement.update_model(
            model_id=api_model_name, 
            model_region="",
            prompt_template="", 
            input_payload=input_payload,
            output_format=output_format, 
            api_url=api_url, 
            api_header=api_header
        )
        return {
            'success': True,
            'name': api_model_name
        }
    
    # Display form
    display_model_form(
        form_type='update',
        model_type='brclient_api',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="update_brclient_api_test_btn"
    )

def display_update_bedrock_anthropic_model(current_model):
    """Display form for updating a Bedrock Anthropic model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    fields = {
        'api_model_name': {
            'label': 'bedrock_anthropic_model_id',
            'type': 'text_input',
            'value': current_model.model_id,
            'disabled': True,
            'required': True
        },
        'bedrock_region': {
            'label': 'bedrock_anthropic_model_region',
            'type': 'text_input',
            'value': current_model.model_region,
            'disabled': True,
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': current_model.input_payload,
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': current_model.output_format,
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'bedrock_model_name_id': current_model.model_id,
        'bedrock_region': current_model.model_region,
        'input_payload': current_model.input_payload,
        'output_format': current_model.output_format
    }
    
    # Submit action
    def submit_action(api_model_name, bedrock_region, input_payload, output_format, **kwargs):
        ModelManagement.update_model(
            model_id=api_model_name, 
            model_region=bedrock_region,
            prompt_template="", 
            input_payload=input_payload,
            output_format=output_format, 
            api_url="", 
            api_header=""
        )
        return {
            'success': True,
            'name': api_model_name
        }
    
    # Display form
    display_model_form(
        form_type='update',
        model_type='bedrock_anthropic',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="update_bedrock_anthropic_test_btn"
    )

def display_update_bedrock_amazon_model(current_model):
    """Display form for updating a Bedrock Amazon model"""
    language = st.session_state.get('language', 'en')
    
    # Define form fields
    fields = {
        'api_model_name': {
            'label': 'bedrock_amazon_nova_model_id',
            'type': 'text_input',
            'value': current_model.model_id,
            'disabled': True,
            'required': True
        },
        'bedrock_region': {
            'label': 'bedrock_amazon_nova_model_region',
            'type': 'text_input',
            'value': current_model.model_region,
            'disabled': True,
            'required': True
        },
        'input_payload': {
            'label': 'input_payload',
            'type': 'text_area',
            'height': 200,
            'value': current_model.input_payload,
            'required': True
        },
        'output_format': {
            'label': 'output_format',
            'type': 'text_area',
            'height': 100,
            'value': current_model.output_format,
            'required': True
        }
    }
    
    # Test parameters
    test_params = {
        'amazon_model_name': current_model.model_id,
        'bedrock_region': current_model.model_region,
        'input_payload': current_model.input_payload,
        'output_format': current_model.output_format
    }
    
    # Submit action
    def submit_action(api_model_name, bedrock_region, input_payload, output_format, **kwargs):
        ModelManagement.update_model(
            model_id=api_model_name, 
            model_region=bedrock_region,
            prompt_template="", 
            input_payload=input_payload,
            output_format=output_format, 
            api_url="", 
            api_header=""
        )
        return {
            'success': True,
            'name': api_model_name
        }
    
    # Display form
    display_model_form(
        form_type='update',
        model_type='bedrock_amazon',
        fields=fields,
        test_params=test_params,
        submit_action=submit_action,
        test_btn_key="update_bedrock_amazon_test_btn"
    )

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
        elif model_id.startswith("bedrock-api."):
            model_name = model_id[12:]
        elif model_id.startswith("brclient-api."):
            model_name = model_id[13:]
        elif model_id.startswith("bedrock-anthropic."):
            model_name = model_id[18:]
        elif model_id.startswith("bedrock-nova."):
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
    
    # Test button
    test_params = {
        'model_id': model.model_id,
        'text': test_text
    }
    test_model_connection('embedding', test_params, "embedding_update_test_btn")
    
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

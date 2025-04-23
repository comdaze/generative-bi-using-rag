import json
import boto3
import requests
import streamlit as st
from dotenv import load_dotenv
from botocore.config import Config

from nlq.business.model import ModelManagement
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar
from config_files.language_config import get_text

logger = getLogger()


def new_connection_clicked():
    st.session_state.new_model = True
    st.session_state.update_model = False
    st.session_state.current_model = None


def sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    connect_flag = False
    connect_info = "-1"
    try:
        if sagemaker_name.startswith("sagemaker."):
            sagemaker_name = sagemaker_name[10:]
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        prompt = prompt_template.replace("SYSTEM_PROMPT", system_prompt).replace("USER_PROMPT", user_prompt)
        input_payload = json.loads(input_payload)
        input_payload_text = json.dumps(input_payload)
        input_payload_text = input_payload_text.replace("\"INPUT\"", json.dumps(prompt))
        sagemaker_client = boto3.client(service_name='sagemaker-runtime', region_name=sagemaker_region)
        response = sagemaker_client.invoke_endpoint(
            EndpointName=sagemaker_name,
            Body=input_payload_text,
            ContentType="application/json",
        )
        response = json.loads(response.get('Body').read())
        answer = eval(output_format)
        connect_info = answer
        connect_flag = True
    except Exception as e:
        logger.error("Failed to connect: {}".format(e))
        connect_info = str(e)
    return connect_flag, connect_info


def api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    connect_flag = False
    connect_info = "-1"
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
        connect_info = answer
        connect_flag = True
    except Exception as e:
        logger.error("Failed to connect: {}".format(e))
        connect_info = str(e)
    return connect_flag, connect_info


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


def test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language)):
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


def test_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language)):
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
        connect_flag, connect_info = api_model_connect(api_model_name, api_url, api_header, input_payload,
                                                       output_format)
        if connect_flag:
            st.success(get_text("connected_successfully", language))
        else:
            st.error(get_text("failed_to_connect", language))
        st.write(connect_info)


def test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language)):
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


def bedrock_anthropic_model_connect(bedrock_model_name_id, bedrock_region, input_payload, output_format):
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
        logger.error("Failed to connect: {}".format(e))
        return False, str(e)


def bedrock_amazon_model_connect(bedrock_model_name_id, bedrock_region, input_payload, output_format):
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
        response_info = bedrock.invoke_model(body=body, modelId=bedrock_model_name_id)
        response = json.loads(response_info.get('body').read())
        answer = eval(output_format)
        return True, answer
    except Exception as e:
        logger.error("Failed to connect: {}".format(e))
        return False, str(e)


def test_bedrock_anthropic_model_connect(bedrock_model_name_id, bedrock_region, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language)):
        if bedrock_model_name_id == '':
            st.error(get_text("required_error", language).format(get_text("bedrock_anthropic_model_id", language)))
        elif bedrock_region == '':
            st.error(get_text("required_error", language).format(get_text("bedrock_anthropic_model_region", language)))
        connect_flag, connect_info = bedrock_anthropic_model_connect(bedrock_model_name_id, bedrock_region, input_payload, output_format)
        if connect_flag:
            st.success(get_text("connected_successfully", language))
        else:
            st.error(get_text("failed_to_connect", language))
        st.write(connect_info)


def test_bedrock_amazon_model_connect(amazon_model_name, bedrock_region, input_payload, output_format):
    language = st.session_state.get('language', 'en')
    if st.button(get_text("model_connection_test", language)):
        if amazon_model_name == '':
            st.error(get_text("required_error", language).format(get_text("bedrock_amazon_nova_model_id", language)))
        elif bedrock_region == '':
            st.error(get_text("required_error", language).format(get_text("bedrock_amazon_nova_model_region", language)))
        elif input_payload == '':
            st.error(get_text("required_error", language).format(get_text("input_payload", language)))
        elif output_format == '':
            st.error(get_text("required_error", language).format(get_text("output_format", language)))
        connect_flag, connect_info = bedrock_amazon_model_connect(amazon_model_name, bedrock_region, input_payload,
                                                                  output_format)
        if connect_flag:
            st.success(get_text("connected_successfully", language))
        else:
            st.error(get_text("failed_to_connect", language))
        st.write(connect_info)


def main():
    load_dotenv()
    language = st.session_state.get('language', 'en')
    st.set_page_config(page_title=get_text("model_management_title", language))
    make_sidebar()

    if 'new_model' not in st.session_state:
        st.session_state['new_model'] = False

    if 'update_model' not in st.session_state:
        st.session_state['update_model'] = False

    if 'current_model' not in st.session_state:
        st.session_state['current_model'] = None

    if "model_list" not in st.session_state:
        st.session_state.model_list = ModelManagement.get_all_models()

    if 'profiles' not in st.session_state:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())

    with st.sidebar:
        st.title(get_text("model_management_title", language))
        st.selectbox(get_text("model_select", language), st.session_state.model_list,
                     index=None,
                     placeholder=get_text("select_model", language), key='current_model_name')
        if st.session_state.current_model_name:
            st.session_state.current_model = ModelManagement.get_model_by_id(st.session_state.current_model_name)
            st.session_state.update_model = True
            st.session_state.new_model = False

        st.button(get_text("create_new_model", language), on_click=new_connection_clicked)

    if st.session_state.new_model:
        st.subheader(get_text("new_model", language))
        model_type_list = [get_text("sagemaker", language), get_text("bedrock_api", language), 
                          get_text("br_client_api", language), get_text("bedrock_anthropic_model", language),
                          get_text("bedrock_amazon_model", language)]
        model_type = st.selectbox(get_text("model_type", language), model_type_list, index=0)
        if model_type == get_text("sagemaker", language):
            sagemaker_name = st.text_input(get_text("sagemaker_endpoint_name", language))
            sagemaker_region = st.text_input(get_text("sagemaker_endpoint_region", language))
            prompt_template = st.text_area(get_text("prompt_template", language),
                                           placeholder=get_text("prompt_template_placeholder", language),
                                           height=200,
                                           help=get_text("prompt_template_help", language))
            example_input = {"inputs": "INPUT", "parameters": {"max_new_tokens": 256}}
            input_payload = st.text_area(get_text("input_payload", language),
                                         placeholder=get_text("input_payload_placeholder", language) + " " + json.dumps(example_input),
                                         height=200,
                                         help=get_text("input_payload_help", language))
            output_format = st.text_area(get_text("output_format", language),
                                         placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                         height=100,
                                         help="Enter output format, The output value name is response")

            test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload,
                                         output_format)

            if st.button(get_text("add_connection", language), type='primary'):
                if sagemaker_name == '':
                    st.error(get_text("required_error", language).format(get_text("sagemaker_endpoint_name", language)))
                elif sagemaker_region == '':
                    st.error(get_text("required_error", language).format(get_text("sagemaker_endpoint_region", language)))
                elif input_payload == '':
                    st.error(get_text("required_error", language).format(get_text("input_payload", language)))
                elif output_format == '':
                    st.error(get_text("required_error", language).format(get_text("output_format", language)))
                else:
                    ModelManagement.add_sagemaker_model(model_id="sagemaker." + sagemaker_name,
                                                        model_region=sagemaker_region,
                                                        prompt_template=prompt_template, input_payload=input_payload,
                                                        output_format=output_format)
                    st.success(get_text("added_successfully", language).format(sagemaker_name))
                    st.session_state.model_list.append("sagemaker." + sagemaker_name)
                    st.session_state.new_connection_mode = False

                    with st.spinner(get_text("update_prompt", language)):
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        for item in all_profiles:
                            profile_name = item
                            profile_value = all_profiles[profile_name]
                            profile_prompt_map = profile_value["prompt_map"]
                            update_prompt_map = {}
                            for each_process in profile_prompt_map:
                                update_prompt_map[each_process] = profile_prompt_map[each_process]
                                update_prompt_map[each_process]["system_prompt"][sagemaker_name] = \
                                    profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
                                update_prompt_map[each_process]["user_prompt"][sagemaker_name] = \
                                    profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
                            ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                        st.success(get_text("prompt_added_successfully", language))
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success(get_text("profiles_update_successfully", language))
        elif model_type == get_text("bedrock_api", language):
            api_model_name = st.text_input(get_text("api_model_name", language))
            api_url = st.text_input(get_text("api_url", language))
            header_value = {"Content-Type": "application/json"}
            api_header = st.text_area(get_text("api_header", language),
                                      height=200,
                                      value=json.dumps(header_value),
                                      help="Enter API Header, json format")

            messages = {"role": "user", "content": "USER_PROMPT"}
            example_input = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 2024, "system": "SYSTEM_PROMPT",
                             "messages": [messages], "temperature": 0.01}
            st.write("The Input Payload is Json format str, Parameters can be modified, but do not change the format")
            input_payload = st.text_area("Mode Input Payload", value=json.dumps(example_input),
                                         height=200,
                                         help="Enter input payload in JSON dumps str")

            output_format = st.text_area("Model Output Format",
                                         value="response.get('content')[0].get('text')",
                                         placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                         height=100,
                                         help="Enter output format, The output value name is response")

            test_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)

            if st.button('Add Connection', type='primary'):
                if api_model_name == '':
                    st.error("api_model_name is required!")
                elif api_url == '':
                    st.error("SageMaker region is required!")
                elif input_payload == '':
                    st.error("Input payload is required!")
                elif output_format == '':
                    st.error("Output format is required!")
                else:
                    ModelManagement.add_api_model(model_id="bedrock-api." + api_model_name, api_url=api_url,
                                                  api_header=api_header, input_payload=input_payload,
                                                  output_format=output_format)
                    st.success(get_text("added_successfully", language).format(api_model_name))
                    st.session_state.model_list.append("bedrock-api." + api_model_name)
                    st.session_state.new_connection_mode = False

                    with st.spinner(get_text("update_prompt", language)):
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        for item in all_profiles:
                            profile_name = item
                            profile_value = all_profiles[profile_name]
                            profile_prompt_map = profile_value["prompt_map"]
                            update_prompt_map = {}
                            for each_process in profile_prompt_map:
                                update_prompt_map[each_process] = profile_prompt_map[each_process]
                                update_prompt_map[each_process]["system_prompt"][api_model_name] = \
                                    profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
                                update_prompt_map[each_process]["user_prompt"][api_model_name] = \
                                    profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
                            ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                        st.success(get_text("prompt_added_successfully", language))
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success(get_text("profiles_update_successfully", language))

        elif model_type == get_text("br_client_api", language):
            api_model_name = st.text_input(get_text("api_model_name", language))
            api_url = st.text_input(get_text("api_url", language))
            header_value = {"Content-Type": "application/json"}
            api_header = st.text_area(get_text("api_header", language),
                                      height=200,
                                      value=json.dumps(header_value),
                                      help=get_text("api_header_help", language))

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
            input_payload = st.text_area(get_text("input_payload", language), value=json.dumps(example_input),
                                         height=200,
                                         help=get_text("input_payload_help", language))

            output_format = st.text_area(get_text("output_format", language),
                                         value="response.get('choices')[0].get('message').get('content')",
                                         placeholder=get_text("output_format_placeholder", language),
                                         height=100,
                                         help=get_text("output_format_help", language))

            test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)

            if st.button(get_text("add_connection", language), type='primary'):
                if api_model_name == '':
                    st.error(get_text("required_error", language).format(get_text("api_model_name", language)))
                elif api_url == '':
                    st.error(get_text("required_error", language).format(get_text("api_url", language)))
                elif input_payload == '':
                    st.error(get_text("required_error", language).format(get_text("input_payload", language)))
                elif output_format == '':
                    st.error(get_text("required_error", language).format(get_text("output_format", language)))
                else:
                    ModelManagement.add_api_model(model_id="brclient-api." + api_model_name, api_url=api_url,
                                                  api_header=api_header, input_payload=input_payload,
                                                  output_format=output_format)
                    st.success(get_text("added_successfully", language).format(api_model_name))
                    st.session_state.model_list.append("brclient-api." + api_model_name)
                    st.session_state.new_connection_mode = False

                    with st.spinner(get_text("update_prompt", language)):
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        for item in all_profiles:
                            profile_name = item
                            profile_value = all_profiles[profile_name]
                            profile_prompt_map = profile_value["prompt_map"]
                            update_prompt_map = {}
                            for each_process in profile_prompt_map:
                                update_prompt_map[each_process] = profile_prompt_map[each_process]
                                update_prompt_map[each_process]["system_prompt"][api_model_name] = \
                                    profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
                                update_prompt_map[each_process]["user_prompt"][api_model_name] = \
                                    profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
                            ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                        st.success(get_text("prompt_added_successfully", language))
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success(get_text("profiles_update_successfully", language))
        elif model_type == get_text("bedrock_anthropic_model", language):
            bedrock_model_name = st.text_input(get_text("bedrock_anthropic_model_id", language))
            bedrock_region = st.text_input(get_text("bedrock_anthropic_model_region", language))
            user_message = {"role": "user", "content": "USER_PROMPT"}
            messages = [user_message]
            example_input = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "system": "SYSTEM_PROMPT",
                "messages": messages,
                "temperature": 0.01
            }
            input_payload = st.text_area(get_text("input_payload", language), value=json.dumps(example_input),
                                         height=200,
                                         help=get_text("input_payload_help", language))

            output_format = st.text_area(get_text("output_format", language),
                                         value="response.get('content')[0].get('text')",
                                         placeholder=get_text("output_format_placeholder", language),
                                         height=100,
                                         help=get_text("output_format_help", language))

            test_bedrock_anthropic_model_connect(bedrock_model_name, bedrock_region, input_payload, output_format)
            if st.button(get_text("add_connection", language), type='primary'):
                if bedrock_model_name == '':
                    st.error(get_text("required_error", language).format(get_text("bedrock_anthropic_model_id", language)))
                elif bedrock_region == '':
                    st.error(get_text("required_error", language).format(get_text("bedrock_anthropic_model_region", language)))
                elif input_payload == '':
                    st.error(get_text("required_error", language).format(get_text("input_payload", language)))
                elif output_format == '':
                    st.error(get_text("required_error", language).format(get_text("output_format", language)))
                else:
                    ModelManagement.add_bedrock_anthropic_model(model_id="bedrock-anthropic." + bedrock_model_name,
                                                                model_region=bedrock_region)
                    st.success(get_text("added_successfully", language).format(bedrock_model_name))
                    st.session_state.model_list.append("bedrock-anthropic." + bedrock_model_name)
                    st.session_state.new_connection_mode = False
                    with st.spinner(get_text("update_prompt", language)):
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        for item in all_profiles:
                            profile_name = item
                            profile_value = all_profiles[profile_name]
                            profile_prompt_map = profile_value["prompt_map"]
                            update_prompt_map = {}
                            for each_process in profile_prompt_map:
                                update_prompt_map[each_process] = profile_prompt_map[each_process]
                                update_prompt_map[each_process]["system_prompt"][bedrock_model_name] = \
                                    profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
                                update_prompt_map[each_process]["user_prompt"][bedrock_model_name] = \
                                    profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
                            ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                        st.success(get_text("prompt_added_successfully", language))
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success(get_text("profiles_update_successfully", language))

        elif model_type == get_text("bedrock_amazon_model", language):
            amazon_model_name = st.text_input(get_text("bedrock_amazon_nova_model_id", language))
            bedrock_region = st.text_input(get_text("bedrock_amazon_nova_model_region", language))
            system_list = [{"text": "SYSTEM_PROMPT"}]
            message_list = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
            inf_params = {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.01}
            example_input = {
                "schemaVersion": "messages-v1",
                "messages": message_list,
                "system": system_list,
                "inferenceConfig": inf_params,
            }
            input_payload = st.text_area(get_text("input_payload", language), value=json.dumps(example_input),
                                         height=200,
                                         help=get_text("input_payload_help", language))

            output_format = st.text_area(get_text("output_format", language),
                                         value="response['output']['message']['content'][0]['text']",
                                         placeholder=get_text("output_format_placeholder", language),
                                         height=100,
                                         help=get_text("output_format_help", language))
            test_bedrock_amazon_model_connect(amazon_model_name, bedrock_region, input_payload, output_format)
            if st.button(get_text("add_connection", language), type='primary'):
                if amazon_model_name == '':
                    st.error(get_text("required_error", language).format(get_text("bedrock_amazon_nova_model_id", language)))
                elif bedrock_region == '':
                    st.error(get_text("required_error", language).format(get_text("bedrock_amazon_nova_model_region", language)))
                elif input_payload == '':
                    st.error(get_text("required_error", language).format(get_text("input_payload", language)))
                elif output_format == '':
                    st.error(get_text("required_error", language).format(get_text("output_format", language)))
                else:
                    ModelManagement.add_bedrock_nova_model(model_id="bedrock-nova." + amazon_model_name,
                                                           model_region=bedrock_region, input_payload=input_payload,
                                                           output_format=output_format)
                    st.success(get_text("added_successfully", language).format(amazon_model_name))
                    st.session_state.model_list.append("bedrock-nova." + amazon_model_name)
                    st.session_state.new_connection_mode = False
                    with st.spinner(get_text("update_prompt", language)):
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        for item in all_profiles:
                            profile_name = item
                            profile_value = all_profiles[profile_name]
                            profile_prompt_map = profile_value["prompt_map"]
                            update_prompt_map = {}
                            for each_process in profile_prompt_map:
                                update_prompt_map[each_process] = profile_prompt_map[each_process]
                                update_prompt_map[each_process]["system_prompt"][amazon_model_name] = \
                                    profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
                                update_prompt_map[each_process]["user_prompt"][amazon_model_name] = \
                                    profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
                            ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                        st.success(get_text("prompt_added_successfully", language))
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success(get_text("profiles_update_successfully", language))

    elif st.session_state.update_model:
        st.subheader(get_text("update_model_connection_title", language))
        if st.session_state.current_model_name.startswith("bedrock-api."):
            model_type = get_text("bedrock_api", language)
        elif st.session_state.current_model_name.startswith("sagemaker."):
            model_type = get_text("sagemaker", language)
        elif st.session_state.current_model_name.startswith("brclient-api."):
            model_type = get_text("br_client_api", language)
        elif st.session_state.current_model_name.startswith("bedrock-anthropic."):
            model_type = get_text("bedrock_anthropic_model", language)
        elif st.session_state.current_model_name.startswith("bedrock-nova."):
            model_type = get_text("bedrock_amazon_model", language)
        else:
            model_type = "-1"
        now_model_name = ""
        if model_type == get_text("sagemaker", language):
            current_model = st.session_state.current_model
            sagemaker_name = st.text_input(get_text("sagemaker_endpoint_name", language), current_model.model_id, disabled=True)
            sagemaker_region = st.text_input(get_text("sagemaker_endpoint_region", language), current_model.model_region, disabled=True)
            prompt_template = st.text_area(get_text("prompt_template", language), current_model.prompt_template, height=200)
            input_payload = st.text_area(get_text("input_payload", language), current_model.input_payload, height=200)
            output_format = st.text_area(get_text("output_format", language), current_model.output_format, height=100)
            test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload,
                                         output_format)
            now_model_name = sagemaker_name

            if st.button(get_text("update_model_connection", language), type='primary'):
                ModelManagement.update_model(model_id=sagemaker_name, model_region=sagemaker_region,
                                             prompt_template=prompt_template, input_payload=input_payload,
                                             output_format=output_format, api_url="", api_header="")
                st.success(get_text("updated_successfully", language).format(sagemaker_name))
        elif model_type == get_text("bedrock_api", language):
            current_model = st.session_state.current_model
            api_model_name = st.text_input(get_text("api_model_name", language), current_model.model_id, disabled=True)
            api_url = st.text_input(get_text("api_url", language), current_model.api_url, disabled=True)
            api_header = st.text_area(get_text("api_header", language), current_model.api_header, height=200)
            input_payload = st.text_area(get_text("input_payload", language), current_model.input_payload, height=200)
            output_format = st.text_area(get_text("output_format", language), current_model.output_format, height=100)
            test_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)
            now_model_name = api_model_name

            if st.button(get_text("update_model_connection", language), type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region="",
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url=api_url, api_header=api_header)
                st.success(get_text("updated_successfully", language).format(api_model_name))
        elif model_type == get_text("br_client_api", language):
            current_model = st.session_state.current_model
            api_model_name = st.text_input(get_text("api_model_name", language), current_model.model_id, disabled=True)
            api_url = st.text_input(get_text("api_url", language), current_model.api_url, disabled=True)
            api_header = st.text_area(get_text("api_header", language), current_model.api_header, height=200)
            input_payload = st.text_area(get_text("input_payload", language), current_model.input_payload, height=200)
            output_format = st.text_area(get_text("output_format", language), current_model.output_format, height=100)
            test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)
            now_model_name = api_model_name

            if st.button(get_text("update_model_connection", language), type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region="",
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url=api_url, api_header=api_header)
                st.success(get_text("updated_successfully", language).format(api_model_name))
        elif model_type == get_text("bedrock_anthropic_model", language):
            current_model = st.session_state.current_model
            api_model_name = st.text_input(get_text("bedrock_anthropic_model_id", language), current_model.model_id, disabled=True)
            bedrock_region = st.text_input(get_text("bedrock_anthropic_model_region", language), current_model.model_region,
                                           disabled=True)
            input_payload = st.text_area(get_text("input_payload", language), current_model.input_payload, height=200)
            output_format = st.text_area(get_text("output_format", language), current_model.output_format, height=100)
            now_model_name = api_model_name
            if st.button(get_text("update_model_connection", language), type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region=bedrock_region,
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url="", api_header="")
                st.success(get_text("updated_successfully", language).format(api_model_name))

        elif model_type == get_text("bedrock_amazon_model", language):
            current_model = st.session_state.current_model
            api_model_name = st.text_input(get_text("bedrock_amazon_nova_model_id", language), current_model.model_id, disabled=True)
            bedrock_region = st.text_input(get_text("bedrock_amazon_nova_model_region", language), current_model.model_region, disabled=True)
            input_payload = st.text_area(get_text("input_payload", language), current_model.input_payload, height=200)
            output_format = st.text_area(get_text("output_format", language), current_model.output_format, height=100)
            now_model_name = api_model_name
            if st.button(get_text("update_model_connection", language), type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region=bedrock_region,
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url="", api_header="")
                st.success(get_text("updated_successfully", language).format(api_model_name))

        if st.button(get_text("delete_model_connection", language)):
            ModelManagement.delete_model(now_model_name)
            st.success(get_text("deleted_successfully", language).format(now_model_name))
            if now_model_name in st.session_state.model_list:
                st.session_state.model_list.remove(now_model_name)
            st.session_state.current_model = None
            with st.spinner(get_text("delete_prompt", language)):
                all_profiles = ProfileManagement.get_all_profiles_with_info()
                if now_model_name.startswith("sagemaker."):
                    now_model_name = now_model_name[10:]
                elif now_model_name.startswith("bedrock-api."):
                    now_model_name = now_model_name[12:]
                elif now_model_name.startswith("brclient-api."):
                    now_model_name = now_model_name[13:]
                elif now_model_name.startswith("bedrock-anthropic."):
                    now_model_name = now_model_name[18:]
                elif now_model_name.startswith("bedrock-nova."):
                    now_model_name = now_model_name[13:]
                for item in all_profiles:
                    profile_name = item
                    profile_value = all_profiles[profile_name]
                    profile_prompt_map = profile_value["prompt_map"]
                    update_prompt_map = {}
                    for each_process in profile_prompt_map:
                        update_prompt_map[each_process] = profile_prompt_map[each_process]
                        if now_model_name in update_prompt_map[each_process]["system_prompt"]:
                            del update_prompt_map[each_process]["system_prompt"][now_model_name]
                        if now_model_name in update_prompt_map[each_process]["user_prompt"]:
                            del update_prompt_map[each_process]["user_prompt"][now_model_name]
                    ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                all_profiles = ProfileManagement.get_all_profiles_with_info()
                st.session_state['profiles'] = all_profiles
                st.success(get_text("prompt_delete_successfully", language))
                st.session_state.samaker_model = ModelManagement.get_all_models()
        st.session_state.update_model = False
    else:
        language = st.session_state.get('language', 'en')
        st.subheader(get_text("model_management_title", language))
        st.info(get_text("select_connection_sidebar", language))


if __name__ == '__main__':
    main()

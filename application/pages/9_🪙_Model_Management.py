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
    if st.button('Model Connection Test'):
        if sagemaker_name == '':
            st.error("SageMaker Endpoint is required!")
        elif sagemaker_region == '':
            st.error("SageMaker region is required!")
        elif input_payload == '':
            st.error("Input payload is required!")
        elif output_format == '':
            st.error("Output format is required!")
        connect_flag, connect_info = sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template,
                                                             input_payload,
                                                             output_format)
        if connect_flag:
            st.success(f"Connected successfully!")
        else:
            st.error(f"Failed to connect!")
        st.write(connect_info)


def test_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    if st.button('Model Connection Test'):
        if api_model_name == '':
            st.error("API Model Name is required!")
        elif api_url == '':
            st.error("API URL is required!")
        elif api_header == '':
            st.error("API Header is required!")
        elif input_payload == '':
            st.error("Input Payload is required!")
        elif output_format == '':
            st.error("Output format is required!")
        connect_flag, connect_info = api_model_connect(api_model_name, api_url, api_header, input_payload,
                                                       output_format)
        if connect_flag:
            st.success(f"Connected successfully!")
        else:
            st.error(f"Failed to connect!")
        st.write(connect_info)


def test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format):
    if st.button('Model Connection Test'):
        if api_model_name == '':
            st.error("API Model Name is required!")
        elif api_url == '':
            st.error("API URL is required!")
        elif api_header == '':
            st.error("API Header is required!")
        elif input_payload == '':
            st.error("Input Payload is required!")
        elif output_format == '':
            st.error("Output format is required!")
        connect_flag, connect_info = other_api_model_connect(api_model_name, api_url, api_header, input_payload,
                                                             output_format)
        if connect_flag:
            st.success(f"Connected successfully!")
        else:
            st.error(f"Failed to connect!")
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
    if st.button('Model Connection Test'):
        if bedrock_model_name_id == '':
            st.error("BedRock Anthropic Model ID is required!")
        elif bedrock_region == '':
            st.error("BedRock Anthropic Model Region is required!")
        connect_flag, connect_info = bedrock_anthropic_model_connect(bedrock_model_name_id, bedrock_region, input_payload, output_format)
        if connect_flag:
            st.success(f"Connected successfully!")
        else:
            st.error(f"Failed to connect!")
        st.write(connect_info)


def test_bedrock_amazon_model_connect(amazon_model_name, bedrock_region, input_payload, output_format):
    if st.button('Model Connection Test'):
        if amazon_model_name == '':
            st.error("BedRock Amazon Model ID is required!")
        elif bedrock_region == '':
            st.error("BedRock Amazon Model Region is required!")
        elif input_payload == '':
            st.error("Input Payload is required!")
        elif output_format == '':
            st.error("Output format is required!")
        connect_flag, connect_info = bedrock_amazon_model_connect(amazon_model_name, bedrock_region, input_payload,
                                                                  output_format)
        if connect_flag:
            st.success(f"Connected successfully!")
        else:
            st.error(f"Failed to connect!")
        st.write(connect_info)


def main():
    load_dotenv()

    st.set_page_config(page_title="Model Management")
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
        st.title("Model Management")
        st.selectbox("Model Select", st.session_state.model_list,
                     index=None,
                     placeholder="Please Select Model...", key='current_model_name')
        if st.session_state.current_model_name:
            st.session_state.current_model = ModelManagement.get_model_by_id(st.session_state.current_model_name)
            st.session_state.update_model = True
            st.session_state.new_model = False

        st.button('Create New Model Conf', on_click=new_connection_clicked)

    if st.session_state.new_model:
        st.subheader("New Model")
        model_type_list = ["Sagemaker", "Bedrock API", "BR Client API", "BedRock Anthropic Model",
                           "BedRock Amazon Model"]
        model_type = st.selectbox("Model Type", model_type_list, index=0)
        if model_type == "Sagemaker":
            sagemaker_name = st.text_input("SageMaker Endpoint Name")
            sagemaker_region = st.text_input("SageMaker Endpoint Region")
            prompt_template = st.text_area("Prompt Template",
                                           placeholder="Enter prompt template, need contain SYSTEM_PROMPT Placeholder and USER_PROMPT Placeholder. \n For Example: SYSTEM_PROMPT<|im_start|>user\nUSER_PROMPT<|im_end|>\n<|im_start|>assistant\n",
                                           height=200,
                                           help="Enter prompt template, need contain SYSTEM_PROMPT Placeholder and USER_PROMPT Placeholder")
            example_input = {"inputs": "INPUT", "parameters": {"max_new_tokens": 256}}
            input_payload = st.text_area("Mode Input Payload",
                                         placeholder="Enter input payload in JSON dumps str, The input text use INPUT Placeholder. For Example: " + json.dumps(
                                             example_input),
                                         height=200,
                                         help="Enter input payload in JSON dumps str, The input text use INPUT Placeholder")
            output_format = st.text_area("Model Output Format",
                                         placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                         height=100,
                                         help="Enter output format, The output value name is response")

            test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload,
                                         output_format)

            if st.button('Add Connection', type='primary'):
                if sagemaker_name == '':
                    st.error("SageMaker name is required!")
                elif sagemaker_region == '':
                    st.error("SageMaker region is required!")
                elif input_payload == '':
                    st.error("Input payload is required!")
                elif output_format == '':
                    st.error("Output format is required!")
                else:
                    ModelManagement.add_sagemaker_model(model_id="sagemaker." + sagemaker_name,
                                                        model_region=sagemaker_region,
                                                        prompt_template=prompt_template, input_payload=input_payload,
                                                        output_format=output_format)
                    st.success(f"{sagemaker_name} added successfully!")
                    st.session_state.model_list.append("sagemaker." + sagemaker_name)
                    st.session_state.new_connection_mode = False

                    with st.spinner('Update Prompt...'):
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
                        st.success("Prompt added successfully!")
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success("profiles update successfully!")
        elif model_type == "Bedrock API":
            api_model_name = st.text_input("API Model Name")
            api_url = st.text_input("API URL")
            header_value = {"Content-Type": "application/json"}
            api_header = st.text_area("API Header",
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
                    st.success(f"{api_model_name} added successfully!")
                    st.session_state.model_list.append("bedrock-api." + api_model_name)
                    st.session_state.new_connection_mode = False

                    with st.spinner('Update Prompt...'):
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
                        st.success("Prompt added successfully!")
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success("profiles update successfully!")

        elif model_type == "BR Client API":
            api_model_name = st.text_input("API Model Name")
            api_url = st.text_input("API URL")
            header_value = {"Content-Type": "application/json"}
            api_header = st.text_area("API Header",
                                      height=200,
                                      value=json.dumps(header_value),
                                      help="Enter API Header, json format")

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

            st.write("The Input Payload is Json format str, Parameters can be modified, but do not change the format")
            input_payload = st.text_area("Mode Input Payload", value=json.dumps(example_input),
                                         height=200,
                                         help="Enter input payload in JSON dumps str")

            output_format = st.text_area("Model Output Format",
                                         value="response.get('choices')[0].get('message').get('content')",
                                         placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                         height=100,
                                         help="Enter output format, The output value name is response")

            test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)

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
                    ModelManagement.add_api_model(model_id="brclient-api." + api_model_name, api_url=api_url,
                                                  api_header=api_header, input_payload=input_payload,
                                                  output_format=output_format)
                    st.success(f"{api_model_name} added successfully!")
                    st.session_state.model_list.append("brclient-api." + api_model_name)
                    st.session_state.new_connection_mode = False

                    with st.spinner('Update Prompt...'):
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
                        st.success("Prompt added successfully!")
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success("profiles update successfully!")
        elif model_type == "BedRock Anthropic Model":
            bedrock_model_name = st.text_input("BedRock Anthropic Model ID")
            bedrock_region = st.text_input("BedRock Anthropic Model Region")
            user_message = {"role": "user", "content": "USER_PROMPT"}
            messages = [user_message]
            example_input = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "system": "SYSTEM_PROMPT",
                "messages": messages,
                "temperature": 0.01
            }
            input_payload = st.text_area("Mode Input Payload", value=json.dumps(example_input),
                                         height=200,
                                         help="Enter input payload in JSON dumps str")

            output_format = st.text_area("Model Output Format",
                                         value="response.get('content')[0].get('text')",
                                         placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                         height=100,
                                         help="Enter output format, The output value name is response")

            test_bedrock_anthropic_model_connect(bedrock_model_name, bedrock_region, input_payload, output_format)
            if st.button('Add Connection', type='primary'):
                if bedrock_model_name == '':
                    st.error("BedRock Anthropic Model ID is required!")
                elif bedrock_region == '':
                    st.error("BedRock Anthropic Model Region is required!")
                elif input_payload == '':
                    st.error("Input payload is required!")
                elif output_format == '':
                    st.error("Output format is required!")
                else:
                    ModelManagement.add_bedrock_anthropic_model(model_id="bedrock-anthropic." + bedrock_model_name,
                                                                model_region=bedrock_region)
                    st.success(f"{bedrock_model_name} added successfully!")
                    st.session_state.model_list.append("bedrock-anthropic." + bedrock_model_name)
                    st.session_state.new_connection_mode = False
                    with st.spinner('Update Prompt...'):
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
                        st.success("Prompt added successfully!")
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success("profiles update successfully!")

        elif model_type == "BedRock Amazon Model":
            amazon_model_name = st.text_input("BedRock Amazon Nova Model ID")
            bedrock_region = st.text_input("BedRock Amazon Nova Model Region")
            system_list = [{"text": "SYSTEM_PROMPT"}]
            message_list = [{"role": "user", "content": [{"text": "USER_PROMPT"}]}]
            inf_params = {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.01}
            example_input = {
                "schemaVersion": "messages-v1",
                "messages": message_list,
                "system": system_list,
                "inferenceConfig": inf_params,
            }
            input_payload = st.text_area("Mode Input Payload", value=json.dumps(example_input),
                                         height=200,
                                         help="Enter input payload in JSON dumps str")

            output_format = st.text_area("Model Output Format",
                                         value="response['output']['message']['content'][0]['text']",
                                         placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                         height=100,
                                         help="Enter output format, The output value name is response")
            test_bedrock_amazon_model_connect(amazon_model_name, bedrock_region, input_payload, output_format)
            if st.button('Add Connection', type='primary'):
                if amazon_model_name == '':
                    st.error("BedRock Amazon Model ID is required!")
                elif bedrock_region == '':
                    st.error("BedRock Anthropic Model Region is required!")
                elif input_payload == '':
                    st.error("Input payload is required!")
                elif output_format == '':
                    st.error("Output format is required!")
                else:
                    ModelManagement.add_bedrock_nova_model(model_id="bedrock-nova." + amazon_model_name,
                                                           model_region=bedrock_region, input_payload=input_payload,
                                                           output_format=output_format)
                    st.success(f"{amazon_model_name} added successfully!")
                    st.session_state.model_list.append("bedrock-nova." + amazon_model_name)
                    st.session_state.new_connection_mode = False
                    with st.spinner('Update Prompt...'):
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
                        st.success("Prompt added successfully!")
                        st.session_state.samaker_model = ModelManagement.get_all_models()
                        all_profiles = ProfileManagement.get_all_profiles_with_info()
                        st.session_state['profiles'] = all_profiles
                        st.success("profiles update successfully!")

    elif st.session_state.update_model:
        st.subheader("Update Model Connection")
        if st.session_state.current_model_name.startswith("bedrock-api."):
            model_type = "Bedrock API"
        elif st.session_state.current_model_name.startswith("sagemaker."):
            model_type = "Sagemaker"
        elif st.session_state.current_model_name.startswith("brclient-api."):
            model_type = "BRClient API"
        elif st.session_state.current_model_name.startswith("bedrock-anthropic."):
            model_type = "BedRock Anthropic Model"
        elif st.session_state.current_model_name.startswith("bedrock-nova."):
            model_type = "BedRock Amazon Model"
        else:
            model_type = "-1"
        now_model_name = ""
        if model_type == "Sagemaker":
            current_model = st.session_state.current_model
            sagemaker_name = st.text_input("SageMaker Endpoint Name", current_model.model_id, disabled=True)
            sagemaker_region = st.text_input("SageMaker Endpoint Region", current_model.model_region, disabled=True)
            prompt_template = st.text_area("Prompt Template", current_model.prompt_template, height=200)
            input_payload = st.text_area("Mode Input Payload", current_model.input_payload, height=200)
            output_format = st.text_area("Model Output Format", current_model.output_format, height=100)
            test_sagemaker_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload,
                                         output_format)
            now_model_name = sagemaker_name

            if st.button('Update Model Connection', type='primary'):
                ModelManagement.update_model(model_id=sagemaker_name, model_region=sagemaker_region,
                                             prompt_template=prompt_template, input_payload=input_payload,
                                             output_format=output_format, api_url="", api_header="")
                st.success(f"{sagemaker_name} updated successfully!")
        elif model_type == "Bedrock API":
            current_model = st.session_state.current_model
            api_model_name = st.text_input("API Model Name", current_model.model_id, disabled=True)
            api_url = st.text_input("API URL", current_model.api_url, disabled=True)
            api_header = st.text_area("API Header", current_model.api_header, height=200)
            input_payload = st.text_area("Mode Input Payload", current_model.input_payload, height=200)
            output_format = st.text_area("Model Output Format", current_model.output_format, height=100)
            test_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)
            now_model_name = api_model_name

            if st.button('Update Model Connection', type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region="",
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url=api_url, api_header=api_header)
                st.success(f"{api_model_name} updated successfully!")
        elif model_type == "BRClient API":
            current_model = st.session_state.current_model
            api_model_name = st.text_input("API Model Name", current_model.model_id, disabled=True)
            api_url = st.text_input("API URL", current_model.api_url, disabled=True)
            api_header = st.text_area("API Header", current_model.api_header, height=200)
            input_payload = st.text_area("Mode Input Payload", current_model.input_payload, height=200)
            output_format = st.text_area("Model Output Format", current_model.output_format, height=100)
            test_other_api_model_connect(api_model_name, api_url, api_header, input_payload, output_format)
            now_model_name = api_model_name

            if st.button('Update Model Connection', type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region="",
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url=api_url, api_header=api_header)
                st.success(f"{api_model_name} updated successfully!")
        elif model_type == "BedRock Anthropic Model":
            current_model = st.session_state.current_model
            api_model_name = st.text_input("BedRock Amazon Anthropic Model ID", current_model.model_id, disabled=True)
            bedrock_region = st.text_input("BedRock Amazon Anthropic Model Region", current_model.model_region,
                                           disabled=True)
            input_payload = st.text_area("Mode Input Payload", current_model.input_payload, height=200)
            output_format = st.text_area("Model Output Format", current_model.output_format, height=100)
            now_model_name = api_model_name
            if st.button('Update Model Connection', type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region=bedrock_region,
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url="", api_header="")
                st.success(f"{api_model_name} updated successfully!")

        elif model_type == "BedRock Amazon Model":
            current_model = st.session_state.current_model
            api_model_name = st.text_input("BedRock Amazon Nova Model ID", current_model.model_id, disabled=True)
            bedrock_region = st.text_input("BedRock Amazon Nova Model Region",current_model.model_region, disabled=True)
            input_payload = st.text_area("Mode Input Payload", current_model.input_payload, height=200)
            output_format = st.text_area("Model Output Format", current_model.output_format, height=100)
            now_model_name = api_model_name
            if st.button('Update Model Connection', type='primary'):
                ModelManagement.update_model(model_id=api_model_name, model_region=bedrock_region,
                                             prompt_template="", input_payload=input_payload,
                                             output_format=output_format, api_url="", api_header="")
                st.success(f"{api_model_name} updated successfully!")

        if st.button('Delete Model Connection'):
            ModelManagement.delete_model(now_model_name)
            st.success(f"{now_model_name} deleted successfully!")
            if now_model_name in st.session_state.model_list:
                st.session_state.model_list.remove(now_model_name)
            st.session_state.current_model = None
            with st.spinner('Delete Prompt...'):
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
                st.success("Prompt delete successfully!")
                st.session_state.samaker_model = ModelManagement.get_all_models()
        st.session_state.update_model = False
    else:
        st.subheader("SageMaker Model Management")
        st.info('Please select model in the left sidebar.')


if __name__ == '__main__':
    main()

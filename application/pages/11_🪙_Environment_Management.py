import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar

logger = getLogger()

system_environment = [
    "{dialect}", "{dialect_prompt}", "{sql_schema}",  "{sql_schema}", "{examples}",
    "{ner_info}", "{sql_guidance}", "{question}", "{table_schema_data}", "{example_data}",
    "{data}", "{chat_history}"
]

def delete_environment(profile_name, environment_name):
    prompt_environment_dict = st.session_state["prompt_environment_dict"][profile_name]
    if environment_name in prompt_environment_dict:
        del prompt_environment_dict[environment_name]
    ProfileManagement.update_table_prompt_environment(profile_name, prompt_environment_dict)
    st.session_state["prompt_environment_dict"][profile_name] = prompt_environment_dict
    st.success(f'Environment {id} deleted.')


@st.dialog("Modify the Environment Value")
def edit_environment(profile, environment_name, environment_value):
    prompt_environment_dict = st.session_state["prompt_environment_dict"][profile]
    environment_name = st.text_input('Environment Name', value=environment_name, disabled=True)
    environment_value = st.text_area('Environment Value', value=environment_value, height=300)
    left_button, right_button = st.columns([1, 2])
    with right_button:
        if st.button("Submit"):
            prompt_environment_dict[environment_name] = environment_value
            ProfileManagement.update_table_prompt_environment(profile, prompt_environment_dict)
            st.success("Sample updated successfully!")
            st.rerun()
    with left_button:
        if st.button("Cancel"):
            st.rerun()


def main():
    load_dotenv()
    logger.info('start prompt environment management')
    st.set_page_config(page_title="Prompt Environment Management")
    make_sidebar()

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if "prompt_environment_dict" not in st.session_state:
        st.session_state["prompt_environment_dict"] = {}

    if 'profiles' not in st.session_state:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())

    with st.sidebar:
        st.title("Prompt Environment Management")
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox("My Data Profiles", all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox("My Data Profiles", all_profiles_list,
                                           index=None,
                                           placeholder="Please select data profile...", key='current_profile_name')

    if current_profile is not None:
        if current_profile not in st.session_state["prompt_environment_dict"]:
            st.session_state["prompt_environment_dict"][current_profile] = st.session_state['profiles'][
                current_profile]["prompt_environment"]

    environment_view, environment_edit = st.tabs(['Environment View', 'Environment Edit'])

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with environment_view:
            for each_environment in st.session_state["prompt_environment_dict"][current_profile]:
                each_environment_value = st.session_state["prompt_environment_dict"][current_profile].get(
                    each_environment, "")
                with st.expander(each_environment):
                    st.code(each_environment_value)
                    st.button('Edit ' + each_environment, on_click=edit_environment,
                              args=[current_profile, each_environment, each_environment_value])
                    st.button('Delete ' + each_environment, on_click=delete_environment,
                              args=[current_profile, each_environment])
        with environment_edit:
            profile_detail = ProfileManagement.get_profile_by_name(current_profile)
            environment_value_edit = profile_detail.prompt_environment
            with st.form(key='prompt_environment_form'):
                environment_name = st.text_input('Environment Name', key='environment_name')
                environment_value = st.text_area('Environment Value', height=300)
                if st.form_submit_button('Add Prompt Environment', type='primary'):
                    environment_name = environment_name.strip()
                    if len(environment_name) > 2 and environment_name.startswith("{") and environment_name.endswith(
                            "}"):
                        if environment_name in system_environment:
                            st.error('Please use another environment name. This is a system environment name.')
                        else:
                            environment_value_edit[environment_name] = environment_value
                            ProfileManagement.update_table_prompt_environment(current_profile, environment_value_edit)
                            st.session_state["prompt_environment_dict"][current_profile] = environment_value_edit
                            st.rerun()
                    else:
                        st.error('please check environment name for example: {year}')
    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()

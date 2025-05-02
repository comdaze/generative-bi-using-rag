import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar
from config_files.language_config import get_text

logger = getLogger()

system_environment = [
    "{dialect}", "{dialect_prompt}", "{sql_schema}",  "{sql_schema}", "{examples}",
    "{ner_info}", "{sql_guidance}", "{question}", "{table_schema_data}", "{example_data}",
    "{data}", "{chat_history}"
]

def delete_environment(profile_name, environment_name):
    lang = st.session_state.get('language', 'en')
    prompt_environment_dict = st.session_state["prompt_environment_dict"][profile_name]
    if environment_name in prompt_environment_dict:
        del prompt_environment_dict[environment_name]
    ProfileManagement.update_table_prompt_environment(profile_name, prompt_environment_dict)
    st.session_state["prompt_environment_dict"][profile_name] = prompt_environment_dict
    st.success(f'{get_text("environment_deleted", lang)} {environment_name}')


@st.dialog("Modify the Environment Value")
def edit_environment(profile, environment_name, environment_value):
    lang = st.session_state.get('language', 'en')
    prompt_environment_dict = st.session_state["prompt_environment_dict"][profile]
    environment_name = st.text_input(get_text('environment_name_label', lang), value=environment_name, disabled=True)
    environment_value = st.text_area(get_text('environment_value_label', lang), value=environment_value, height=300)
    left_button, right_button = st.columns([1, 2])
    with right_button:
        if st.button(get_text('submit_button', lang)):
            prompt_environment_dict[environment_name] = environment_value
            ProfileManagement.update_table_prompt_environment(profile, prompt_environment_dict)
            st.success(get_text('environment_updated', lang))
            st.rerun()
    with left_button:
        if st.button(get_text('cancel_button', lang)):
            st.rerun()


def main():
    load_dotenv()
    logger.info('start prompt environment management')
    
    # Get current language
    lang = st.session_state.get('language', 'en')
    
    st.set_page_config(page_title=get_text('prompt_environment_title', lang))
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
        st.title(get_text('prompt_environment_title', lang))
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox(get_text('my_data_profiles', lang), all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox(get_text('my_data_profiles', lang), all_profiles_list,
                                           index=None,
                                           placeholder=get_text('select_profile', lang), key='current_profile_name')

    if current_profile is not None:
        if current_profile not in st.session_state["prompt_environment_dict"]:
            st.session_state["prompt_environment_dict"][current_profile] = st.session_state['profiles'][
                current_profile]["prompt_environment"]

    environment_view, environment_edit = st.tabs([get_text('environment_view_tab', lang), get_text('environment_edit_tab', lang)])

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with environment_view:
            for each_environment in st.session_state["prompt_environment_dict"][current_profile]:
                each_environment_value = st.session_state["prompt_environment_dict"][current_profile].get(
                    each_environment, "")
                with st.expander(each_environment):
                    st.code(each_environment_value)
                    st.button(f"{get_text('edit_button', lang)} {each_environment}", on_click=edit_environment,
                              args=[current_profile, each_environment, each_environment_value])
                    st.button(f"{get_text('delete_button', lang)} {each_environment}", on_click=delete_environment,
                              args=[current_profile, each_environment])
        with environment_edit:
            profile_detail = ProfileManagement.get_profile_by_name(current_profile)
            environment_value_edit = profile_detail.prompt_environment
            with st.form(key='prompt_environment_form'):
                environment_name = st.text_input(get_text('environment_name_label', lang), key='environment_name')
                environment_value = st.text_area(get_text('environment_value_label', lang), height=300)
                if st.form_submit_button(get_text('add_environment_button', lang), type='primary'):
                    environment_name = environment_name.strip()
                    if len(environment_name) > 2 and environment_name.startswith("{") and environment_name.endswith(
                            "}"):
                        if environment_name in system_environment:
                            st.error(get_text('system_environment_error', lang))
                        else:
                            environment_value_edit[environment_name] = environment_value
                            ProfileManagement.update_table_prompt_environment(current_profile, environment_value_edit)
                            st.session_state["prompt_environment_dict"][current_profile] = environment_value_edit
                            st.rerun()
                    else:
                        st.error(get_text('environment_name_format_error', lang))
    else:
        st.info(get_text('select_data_profile_sidebar', lang))


if __name__ == '__main__':
    main()

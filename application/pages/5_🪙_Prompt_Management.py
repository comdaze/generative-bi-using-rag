import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar
from utils.prompts.check_prompt import check_prompt_syntax, find_missing_prompt_syntax
from config_files.language_config import get_text

logger = getLogger()


def main():
    load_dotenv()
    logger.info('start prompt management')
    st.set_page_config(page_title="Prompt Management")
    make_sidebar()
    
    # Get current language
    lang = st.session_state.get('language', 'en')

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if 'profiles' not in st.session_state:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())

    if st.session_state.update_profile:
        logger.info("session_state update_profile get_all_profiles_with_info")
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state["profiles_list"] = list(all_profiles.keys())
        st.session_state['profiles'] = all_profiles
        st.session_state.update_profile = False

    with st.sidebar:
        st.title(get_text('prompt_management_title', lang))
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox(get_text('my_data_profiles', lang), all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox(get_text('my_data_profiles', lang), all_profiles_list,
                                       index=None,
                                       placeholder=get_text('select_profile', lang), key='current_profile_name')

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        profile_detail = ProfileManagement.get_profile_by_name(current_profile)
        prompt_environment = profile_detail.prompt_environment
        prompt_map = profile_detail.prompt_map
        if prompt_map is not None:
            prompt_type_selected_table = st.selectbox(get_text('prompt_type', lang), prompt_map.keys(), index=None,
                                                      format_func=lambda x: prompt_map[x].get('title'),
                                                      placeholder=get_text('select_prompt_type', lang))
            if prompt_type_selected_table is not None:
                single_type_prompt_map = prompt_map.get(prompt_type_selected_table)
                system_prompt = single_type_prompt_map.get('system_prompt')
                model_selected_table = st.selectbox(get_text('llm_model', lang), system_prompt.keys(), index=None,
                                                    placeholder=get_text('select_model', lang))

                if model_selected_table is not None:
                    profile_detail = ProfileManagement.get_profile_by_name(current_profile)
                    prompt_map = profile_detail.prompt_map
                    single_type_prompt_map = prompt_map.get(prompt_type_selected_table)
                    if len(prompt_environment) > 0:
                        with st.expander(get_text('custom_env_variables', lang)):
                            for each_environment in prompt_environment:
                                each_environment_value = prompt_environment.get(each_environment, "")
                                st.write(get_text('environment_name', lang) + each_environment + get_text('environment_value', lang) + each_environment_value)
                    system_prompt = single_type_prompt_map.get('system_prompt')
                    user_prompt = single_type_prompt_map.get('user_prompt')
                    system_prompt_input = st.text_area(get_text('system_prompt', lang), system_prompt[model_selected_table], height=300)
                    user_prompt_input = st.text_area(get_text('user_prompt', lang), user_prompt[model_selected_table], height=500)

                    if st.button(get_text('save_prompt', lang), type='primary'):
                        # check prompt syntax, missing placeholder will cause backend execution failure
                        st.session_state.update_profile = True
                        if check_prompt_syntax(system_prompt_input, user_prompt_input,
                                               prompt_type_selected_table, model_selected_table):
                            # assign new system/user prompt by selected model
                            system_prompt[model_selected_table] = system_prompt_input
                            user_prompt[model_selected_table] = user_prompt_input

                            # save new profile to DynamoDB
                            ProfileManagement.update_table_prompt_map(current_profile, prompt_map)
                            st.success(get_text('saved_prompt', lang))
                        else:
                            # if missing syntax, find all missing ones and print in page
                            missing_system_prompt_syntax, missing_user_prompt_syntax = (
                                find_missing_prompt_syntax(system_prompt_input, user_prompt_input,
                                                           prompt_type_selected_table, model_selected_table))
                            st.error(
                                get_text('failed_save_prompts', lang)
                                .format(missing_system_prompt_syntax, missing_user_prompt_syntax))

    else:
        st.info(get_text('select_data_profile_sidebar', lang))


if __name__ == '__main__':
    main()

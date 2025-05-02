import time

import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from utils.logging import getLogger
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info
from config_files.language_config import get_text

logger = getLogger()

def delete_entity_sample(profile_name, id):
    language = st.session_state.get('language', 'en')
    VectorStore.delete_agent_cot_sample(profile_name, id)
    new_value = []
    for item in st.session_state["cot_sample_search"][profile_name]:
        if item["id"] != id:
            new_value.append(item)
    st.session_state["cot_sample_search"][profile_name] = new_value
    st.success(get_text("cot_info_deleted", language).format(id))

@st.dialog(get_text("modify_sql_value", st.session_state.get('language', 'en')))
def edit_value(profile, entity_item, entity_id):
    language = st.session_state.get('language', 'en')
    query_value = entity_item["query"]
    comment_value = entity_item["comment"]
    query = st.text_input(get_text("query", language), value=query_value)
    comment = st.text_area(get_text("answer", language), value=comment_value, height=300)
    left_button, right_button = st.columns([1, 2])
    with right_button:
        if st.button(get_text("submit", language)):
            if query == query_value:
                VectorStore.add_sample(profile, query, comment)
            else:
                VectorStore.delete_sample(profile, entity_id)
                VectorStore.add_sample(profile, query, comment)
                st.success(get_text("sample_updated", language))
                with st.spinner(get_text("updating_index", language)):
                    time.sleep(2)
                st.session_state["cot_sample_search"][profile] = VectorStore.get_all_samples(profile)
                st.rerun()
    with left_button:
        if st.button(get_text("cancel", language)):
            st.rerun()

def main():
    load_dotenv()
    logger.info('start agent cot management')
    language = st.session_state.get('language', 'en')
    st.set_page_config(page_title=get_text("agent_cot_management_title", language))
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if "cot_sample_search" not in st.session_state:
        st.session_state["cot_sample_search"] = {}

    if 'cot_refresh_view' not in st.session_state:
        st.session_state['cot_refresh_view'] = False

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
        st.title(get_text("agent_cot_management_title", language))
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox(get_text("my_data_profiles", language), all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox(get_text("my_data_profiles", language), all_profiles_list,
                                       index=None,
                                       placeholder=get_text("select_profile", language), key='current_profile_name')

        if current_profile not in st.session_state["cot_sample_search"]:
            st.session_state["cot_sample_search"][current_profile] = None

    if current_profile is not None:
        if st.session_state.cot_refresh_view or st.session_state["cot_sample_search"][current_profile] is None:
            st.session_state["cot_sample_search"][current_profile] = VectorStore.get_all_agent_cot_samples(current_profile)
            st.session_state.cot_refresh_view = False

    tab_view, tab_add, tab_search = st.tabs([
        get_text("view_cot_samples", language), 
        get_text("add_new_cot_sample", language), 
        get_text("cot_sample_search", language)
    ])
    
    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with tab_view:
            if current_profile is not None:
                st.write(get_text("max_display_info", language))
                for sample in st.session_state["cot_sample_search"][current_profile]:
                    # st.write(f"Sample: {sample}")
                    with st.expander(sample['query']):
                        st.code(sample['comment'])
                        st.button(get_text("edit", language) + sample['id'], on_click=edit_value,
                                  args=[current_profile, sample, sample['id']])
                        st.button(get_text("delete", language) + sample['id'], on_click=delete_entity_sample, 
                                  args=[current_profile, sample['id']])

        with tab_add:
            if current_profile is not None:
                with st.form(key='cot_add_form'):
                    query = st.text_input(get_text("query", language), key='index_question')
                    comment = st.text_area(get_text("comment", language), key='index_answer', height=300)

                    if st.form_submit_button(get_text("add_cot_info", language), type='primary'):
                        if len(query) > 0 and len(comment) > 0:
                            VectorStore.add_agent_cot_sample(current_profile, query, comment)
                            st.success(get_text("cot_info_added", language))
                            st.success(get_text("update_index", language))
                            with st.spinner(get_text("updating_index", language)):
                                time.sleep(2)
                            st.session_state["cot_sample_search"][current_profile] = VectorStore.get_all_agent_cot_samples(current_profile)
                            st.rerun()
                        else:
                            st.error(get_text("please_input_valid", language))

        with tab_search:
            if current_profile is not None:
                entity_search = st.text_input(get_text("entity_search", language), key='index_entity_search')
                retrieve_number = st.slider(get_text("entity_retrieve_number", language), 0, 100, 10)
                if st.button(get_text("search", language), type='primary'):
                    if len(entity_search) > 0:
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number, opensearch_info['agent_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['query'],
                                          'Answer': sample['_source']['comment'].strip()}
                            st.code(sample_res)
                            st.button(get_text("delete", language) + sample['_id'], key=sample['_id'], on_click=delete_entity_sample,
                                      args=[current_profile, sample['_id']])
    else:
        st.info(get_text("select_data_profile_sidebar", language))

if __name__ == '__main__':
    main()

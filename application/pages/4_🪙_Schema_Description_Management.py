import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar
from config_files.language_config import get_text

logger = getLogger()

def main():
    load_dotenv()
    logger.info('start schema management')
    st.set_page_config(page_title="Schema Management", )
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
        st.title(get_text('schema_management_title', lang))
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

        selected_table = st.selectbox(get_text('tables', lang), profile_detail.tables, index=None, placeholder=get_text('select_table', lang))
        if selected_table is not None:
            table_info = profile_detail.tables_info[selected_table]
            if table_info is not None:
                table_ddl = table_info['ddl']
                table_desc = table_info['description']
                table_anno = table_info.get('tbl_a')
                column_anno = table_info.get('col_a')

                st.caption(get_text('table_description', lang).format(table_desc))
                tbl_annotation = st.text_input(get_text('table_annotation', lang), table_anno)

                if column_anno is not None:
                    col_annotation_text = column_anno
                    col_annotation = st.text_area(get_text('column_annotation', lang), col_annotation_text, height=500)
                else:
                    col_annotation = st.text_area(get_text('column_annotation', lang), table_ddl, height=400, help=get_text('column_annotation_help', lang))
                if st.button(get_text('save', lang), type='primary'):
                    st.session_state.update_profile = True
                    origin_tables_info = profile_detail.tables_info
                    origin_table_info = origin_tables_info[selected_table]
                    origin_table_info['tbl_a'] = tbl_annotation
                    origin_table_info['col_a'] = col_annotation
                    ProfileManagement.update_table_def(current_profile, origin_tables_info)
                    st.success(get_text('saved', lang))
    else:
        st.info(get_text('select_data_profile_sidebar', lang))

if __name__ == '__main__':
    main()

import streamlit as st
from dotenv import load_dotenv
from nlq.business.connection import ConnectionManagement
from nlq.business.datasource.base import DataSourceBase
from nlq.business.datasource.factory import DataSourceFactory
from nlq.business.profile import ProfileManagement
from utils.logging import getLogger
from utils.navigation import make_sidebar
from config_files.language_config import get_text


logger = getLogger()

def new_profile_clicked():
    st.session_state.profile_page_mode = 'new'
    st.session_state.current_profile_name = None


@st.cache_data
def get_profile_by_name(profile_name):
    return ProfileManagement.get_profile_by_name(profile_name)


@st.cache_data
def get_all_profiles():
    return ProfileManagement.get_all_profiles()


@st.cache_data
def get_conn_config_by_name(conn_name):
    return ConnectionManagement.get_conn_config_by_name(conn_name)


@st.cache_data
def get_all_schemas_by_config(_conn_config, default_values):
    try:
        return ConnectionManagement.get_all_schemas_by_config(_conn_config)
    except Exception as e:
        logger.error(e)
        return default_values


# @st.cache_data
def get_table_name_by_config(_conn_config, schema_names, default_values):
    try:
        return ConnectionManagement.get_table_name_by_config(_conn_config, schema_names)
    except Exception as e:
        logger.error(e)
        return default_values


def show_delete_profile(profile_name, lang):
    if st.button(get_text('delete_profile', lang)):
        st.session_state.update_profile = True
        ProfileManagement.delete_profile(profile_name)
        st.success(get_text('profile_deleted', lang).format(profile_name))
        st.session_state.profile_page_mode = 'default'
        st.cache_data.clear()
        st.rerun()


def main():
    load_dotenv()
    logger.info('start data profile management')
    st.set_page_config(page_title="Data Profile Management", )
    make_sidebar()
    
    # Get current language
    lang = st.session_state.get('language', 'en')

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if 'profile_page_mode' not in st.session_state:
        st.session_state['profile_page_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

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
        st.title(get_text('data_profile_title', lang))
        st.selectbox(get_text('my_data_profiles', lang), get_all_profiles(),
                     index=None,
                     placeholder=get_text('select_profile', lang), key='current_profile_name')
        if st.session_state.current_profile_name:
            st.session_state.profile_page_mode = 'update'

        st.button(get_text('create_new_profile', lang), on_click=new_profile_clicked)

    if st.session_state.profile_page_mode == 'new':
        st.subheader(get_text('create_new_data_profile', lang))
        profile_name = st.text_input(get_text('profile_name', lang))
        selected_conn_name = st.selectbox(get_text('data_connection', lang), ConnectionManagement.get_all_connections(), index=None)

        if selected_conn_name:
            conn_config = ConnectionManagement.get_conn_config_by_name(selected_conn_name)
            schemas_table_dict = ConnectionManagement.get_all_schemas_and_table_by_config(conn_config)
            schemas_list = list(schemas_table_dict.keys())
            schema_names = st.multiselect(get_text('schema_name', lang), schemas_list)
            tables_from_db = []
            if schema_names is not None:
                for schema_name in schema_names:
                    schema_table = schemas_table_dict[schema_name]
                    for each_table in schema_table:
                        tables_from_db.append(schema_name + "." + each_table)
            # tables_from_db = ConnectionManagement.get_table_name_by_config(conn_config, schema_names)
            # selected_tables = st.multiselect("Select tables included in this profile", tables_from_db)
            # comments = st.text_input("Comments")

            with st.form(key='create_profile_form'):
                selected_tables = st.multiselect(get_text('select_tables', lang), tables_from_db)
                comments = st.text_input(get_text('comments', lang))
                create_profile = st.form_submit_button(get_text('create_profile', lang), type='primary')

            if create_profile:
                st.session_state.update_profile = True
                if not selected_tables:
                    st.error(get_text('select_at_least_one_table', lang))
                    return
                selected_tables_info = {}
                for each_item in selected_tables:
                    each_schema, each_table = each_item.rsplit('.', 1)
                    if each_schema not in selected_tables_info:
                        selected_tables_info[each_schema] = []
                    selected_tables_info[each_schema].append(each_table)
                with st.spinner(get_text('creating_profile', lang)):
                    ProfileManagement.add_profile(profile_name, selected_conn_name, schema_names, selected_tables,
                                                  comments, conn_config.db_type)
                    st.success(get_text('profile_created', lang))
                    st.session_state.profile_page_mode = 'default'
                    table_definitions = ConnectionManagement.get_table_definition_by_config(conn_config, selected_tables_info)
                    st.write(table_definitions)
                    ProfileManagement.update_table_def(profile_name, table_definitions, merge_before_update=True)
                    # clear cache
                    st.cache_data.clear()

                # st.session_state.profile_page_mode = 'default'
    elif st.session_state.profile_page_mode == 'update' and st.session_state.current_profile_name is not None:
        st.subheader(get_text('update_data_profile', lang))
        current_profile = get_profile_by_name(st.session_state.current_profile_name)
        profile_name = st.text_input(get_text('profile_name', lang), value=current_profile.profile_name, disabled=True)
        selected_conn_name = st.text_input(get_text('data_connection', lang), value=current_profile.conn_name, disabled=True)
        conn_config = get_conn_config_by_name(selected_conn_name)
        if not conn_config:
            # if the connection record has been deleted, then allow user to delete the profile
            st.error(get_text('connection_not_found', lang))
            show_delete_profile(profile_name, lang)
            return
        schemas_table_dict = ConnectionManagement.get_all_schemas_and_table_by_config(conn_config)
        schemas_list = list(schemas_table_dict.keys())
        schema_names = st.multiselect(get_text('schema_name', lang), schemas_list,
                                      default=current_profile.schemas)
        tables_from_db = []
        if schema_names is not None:
            for schema_name in schema_names:
                schema_table = schemas_table_dict[schema_name]
                for each_table in schema_table:
                    tables_from_db.append(schema_name + "." + each_table)
        # tables_from_db = get_table_name_by_config(conn_config, schema_names, current_profile.tables)
        # make sure all tables defined in profile are existing in the table list of the current database
        intersection_tables = set(tables_from_db) & set(current_profile.tables)
        if len(intersection_tables) < len(current_profile.tables):
            st.warning(get_text('tables_not_exist', lang))
        if len(intersection_tables) == 0:
            intersection_tables = None
        with st.form(key='update_profile_form'):
            selected_tables = st.multiselect(get_text('select_tables', lang), tables_from_db,
                                             default=intersection_tables)
            comments = st.text_area(get_text('comments', lang),
                                    value=current_profile.comments,
                                    placeholder=get_text('comments_placeholder', lang))

            st_enable_rls = False
            rls_config = None
            if DataSourceFactory.get_data_source(conn_config.db_type).support_row_level_security():
                st_enable_rls = st.checkbox(get_text('enable_rls', lang), value=current_profile.enable_row_level_security,
                                            help=get_text('rls_help', lang))
                rls_config = st.text_area(get_text('rls_config', lang),
                                          value=current_profile.row_level_security_config,
                                          placeholder=get_text('rls_placeholder', lang), disabled=not st_enable_rls, height=240)
            update_profile = st.form_submit_button(get_text('update_profile', lang))

        if update_profile:
            st.session_state.update_profile = True
            if not selected_tables:
                st.error(get_text('select_at_least_one_table', lang))
                return
            with st.spinner(get_text('fetching', lang)):
                old_tables_info = ProfileManagement.get_profile_by_name(profile_name).tables_info
                if st_enable_rls:
                    has_validated = DataSourceBase.validate_row_level_security_config(rls_config)
                    if not has_validated:
                        st.error(get_text('invalid_rls_config', lang))
                        return
                ProfileManagement.update_profile(profile_name, selected_conn_name, schema_names, selected_tables,
                                                 comments, old_tables_info, conn_config.db_type, st_enable_rls,
                                                 rls_config)
                st.success(get_text('profile_updated', lang))
                st.cache_data.clear()

        if st.button(get_text('fetch_table_definition', lang)):
            st.session_state.update_profile = True
            if not selected_tables:
                st.error(get_text('select_at_least_one_table', lang))
            selected_tables_info = {}
            for each_item in selected_tables:
                each_schema, each_table = each_item.rsplit('.', 1)
                if each_schema not in selected_tables_info:
                    selected_tables_info[each_schema] = []
                selected_tables_info[each_schema].append(each_table)
            with st.spinner(get_text('fetching', lang)):
                table_definitions = ConnectionManagement.get_table_definition_by_config(conn_config, selected_tables_info)
                st.write(table_definitions)
                ProfileManagement.update_table_def(profile_name, table_definitions, merge_before_update=True)
                st.session_state.profile_page_mode = 'default'
                st.cache_data.clear()

        show_delete_profile(profile_name, lang)
    else:
        st.info(get_text('select_connection_sidebar', lang))


if __name__ == '__main__':
    main()

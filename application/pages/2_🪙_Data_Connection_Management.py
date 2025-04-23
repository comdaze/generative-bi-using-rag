import json

import streamlit as st
from dotenv import load_dotenv
from nlq.business.connection import ConnectionManagement
from nlq.data_access.database import RelationDatabase
from utils.logging import getLogger
from utils.navigation import make_sidebar
from config_files.language_config import get_text

logger = getLogger()
# global variables

db_type_mapping = {
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL',
    'redshift': 'Redshift',
    'starrocks': 'StarRocks',
    'clickhouse': 'Clickhouse',
    'hive': 'Hive',
    'athena': 'Athena',
    'bigquery': 'BigQuery',
    'presto': 'Presto',
    'maxcompute': 'MaxCompute',
    'sqlserver': 'SQLServer'
}


# global functions
def index_of_db_type(db_type):
    index = 0
    for k, v in db_type_mapping.items():
        if k == db_type:
            return index
        index += 1


def new_connection_clicked():
    st.session_state.new_connection_mode = True
    st.session_state.update_connection_mode = False
    st.session_state.current_conn_name = None


def test_connection_view(db_type, user, password, host, port, db_name):
    # Get current language
    lang = st.session_state.get('language', 'en')
    
    if st.button(get_text('test_connection', lang)):
        if RelationDatabase.test_connection(db_type, user, password, host, port, db_name):
            st.success(get_text('connection_success', lang))
        else:
            st.error(get_text('connection_failed', lang).format(""))


# Main logic
def main():
    load_dotenv()

    st.set_page_config(page_title="Data Connection Management")
    make_sidebar()
    
    # Get current language
    lang = st.session_state.get('language', 'en')

    if 'new_connection_mode' not in st.session_state:
        st.session_state['new_connection_mode'] = False

    if 'update_connection_mode' not in st.session_state:
        st.session_state['update_connection_mode'] = False

    if 'current_connection' not in st.session_state:
        st.session_state['current_connection'] = None

    with st.sidebar:
        st.title(get_text('data_connection_title', lang))
        st.selectbox(get_text('connection_list', lang), ConnectionManagement.get_all_connections(),
                     index=None,
                     placeholder=get_text('select_connection', lang), key='current_conn_name')
        if st.session_state.current_conn_name:
            st.session_state.current_connection = ConnectionManagement.get_conn_config_by_name(
                st.session_state.current_conn_name)
            st.session_state.update_connection_mode = True
            st.session_state.new_connection_mode = False

        st.button(get_text('create_new', lang), on_click=new_connection_clicked)

    if st.session_state.new_connection_mode:
        # Get current language
        lang = st.session_state.get('language', 'en')
        
        st.subheader(get_text('new_connection', lang))
        connection_name = st.text_input(get_text('connection_name', lang))
        db_type = st.selectbox(get_text('db_type', lang), db_type_mapping.values(), index=0)
        db_type = db_type.lower()  # Convert to lowercase for matching with db_mapping keys
        if db_type == 'athena':
            st.info("Please enter S3 staging directory in the database name field. You can leave other fields empty. Please also make sure that IAM role is able to access Athena and S3.")

        if db_type == "bigquery":
            host = st.text_input(get_text('host', lang))
            password = st.text_area("Credentials Info", height=200,  placeholder="Paste your credentials info here")
            port = ""
            user = ""
            db_name = ""
            comment = st.text_input(get_text('comment', lang))
            test_connection_view(db_type, user, password, host, port, db_name)
            if st.button(get_text('add_connection', lang), type='primary'):
                ConnectionManagement.add_connection(connection_name, db_type, host, port, user, password, db_name, comment)
                st.success(get_text('connection_added', lang))
                st.session_state.new_connection_mode = False
        elif db_type == "presto":
            host = st.text_input(get_text('host', lang))
            port = st.text_input(get_text('port', lang), placeholder="8889")
            db_name = st.text_input(get_text('database', lang), placeholder="hive/default")
            comment = st.text_input(get_text('comment', lang))

            test_connection_view(db_type, "", "", host, port, db_name)

            if st.button(get_text('add_connection', lang), type='primary'):
                if db_name == '':
                    st.error("Database name is required!")
                else:
                    ConnectionManagement.add_connection(connection_name, db_type, host, port, "", "", db_name, comment)
                    st.success(get_text('connection_added', lang))
                    st.session_state.new_connection_mode = False

        else:
            host = st.text_input(get_text('host', lang))
            port = st.text_input(get_text('port', lang))
            user = st.text_input(get_text('username', lang))
            password = st.text_input(get_text('password', lang), type="password")
            db_name = st.text_input(get_text('database', lang))
            comment = st.text_input(get_text('comment', lang))

            test_connection_view(db_type, user, password, host, port, db_name)

            if st.button(get_text('add_connection', lang), type='primary'):
                if db_name == '':
                    st.error("Database name is required!")
                else:
                    ConnectionManagement.add_connection(connection_name, db_type, host, port, user, password, db_name, comment)
                    st.success(get_text('connection_added', lang))
                    st.session_state.new_connection_mode = False

    elif st.session_state.update_connection_mode:
        # Get current language
        lang = st.session_state.get('language', 'en')
        
        st.subheader(get_text('update_connection_title', lang))
        current_conn = st.session_state.current_connection
        connection_name = st.text_input(get_text('connection_name', lang), current_conn.conn_name, disabled=True)
        db_type = st.selectbox(get_text('db_type', lang), db_type_mapping.values(), index=index_of_db_type(current_conn.db_type),
                               disabled=True)
        db_type = db_type.lower()  # Convert to lowercase for matching with db_mapping keys
        if db_type == 'athena':
            st.info("Please enter S3 staging directory in the database name field. You can leave other fields empty. Please also make sure that IAM role is able to access Athena and S3.")
            host = st.text_input(get_text('host', lang), current_conn.db_host)
            port = st.text_input(get_text('port', lang), current_conn.db_port)
            user = st.text_input(get_text('username', lang), current_conn.db_user)
            password = st.text_input(get_text('password', lang), type="password", value=current_conn.db_pwd)
            db_name = st.text_input(get_text('database', lang), current_conn.db_name)
            comment = st.text_input(get_text('comment', lang), current_conn.comment)
        elif db_type == "bigquery":
            host = st.text_input(get_text('host', lang))
            password = st.text_area("Credentials Info", height=200, value=current_conn.db_pwd)
            port = ""
            user = ""
            db_name = ""
            comment = st.text_input(get_text('comment', lang))
        else:
            host = st.text_input(get_text('host', lang), current_conn.db_host)
            port = st.text_input(get_text('port', lang), current_conn.db_port)
            user = st.text_input(get_text('username', lang), current_conn.db_user)
            password = st.text_input(get_text('password', lang), type="password", value=current_conn.db_pwd)
            db_name = st.text_input(get_text('database', lang), current_conn.db_name)
            comment = st.text_input(get_text('comment', lang), current_conn.comment)

        test_connection_view(db_type, user, password, host, port, db_name)

        if st.button(get_text('update_connection', lang), type='primary'):
            ConnectionManagement.update_connection(connection_name, db_type, host, port, user, password, db_name,
                                                   comment)
            st.success(get_text('connection_added', lang))

        if st.button(get_text('delete_connection', lang)):
            ConnectionManagement.delete_connection(connection_name)
            st.success(get_text('connection_deleted', lang))
            st.session_state.current_connection = None

        st.session_state.update_connection_mode = False

    else:
        # Get current language
        lang = st.session_state.get('language', 'en')
        
        st.subheader(get_text('data_connection_title', lang))
        st.info(get_text('select_connection_sidebar', lang))


if __name__ == '__main__':
    main()

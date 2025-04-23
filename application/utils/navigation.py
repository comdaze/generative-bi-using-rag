import streamlit as st
import streamlit_authenticator as stauth
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
import yaml
from yaml.loader import SafeLoader


def get_authenticator():
    with open('config_files/stauth_config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        float(config['cookie']['expiry_days']),
        config['pre-authorized']
    )


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]


def make_sidebar():
    # Initialize language preference in session state if not already set
    if 'language' not in st.session_state:
        st.session_state['language'] = 'en'
        
    # Get current language
    lang = st.session_state['language']
    
    # Define translations for sidebar items
    sidebar_translations = {
        'en': {
            'index': 'Index',
            'playground': 'Generative BI Playground',
            'data_customization': 'Data Customization Management',
            'data_connection': 'Data Connection Management',
            'data_profile': 'Data Profile Management',
            'schema_description': 'Schema Description Management',
            'prompt_management': 'Prompt Management',
            'prompt_environment': 'Prompt Environment Management',
            'performance_enhancement': 'Performance Enhancement',
            'index_management': 'Index Management',
            'entity_management': 'Entity Management',
            'agent_cot': 'Agent Cot Management',
            'model_management': 'Model Management',
            'user_authorization': 'User Authorization Management',
            'logout': 'Log out',
            'language_selector': 'Language'
        },
        'zh': {
            'index': '首页',
            'playground': '生成式商业智能平台',
            'data_customization': '数据自定义管理',
            'data_connection': '数据连接管理',
            'data_profile': '数据配置文件管理',
            'schema_description': '模式描述管理',
            'prompt_management': '提示词管理',
            'prompt_environment': '提示词环境管理',
            'performance_enhancement': '性能增强',
            'index_management': '索引管理',
            'entity_management': '实体管理',
            'agent_cot': '代理思维链管理',
            'model_management': '模型管理',
            'user_authorization': '用户授权管理',
            'logout': '退出登录',
            'language_selector': '语言'
        }
    }
    
    # Use the appropriate language
    translations = sidebar_translations.get(lang, sidebar_translations['en'])
    
    with st.sidebar:
        # Add language selector at the top of sidebar
        language_options = {'English': 'en', '中文': 'zh'}
        selected_language = st.selectbox(
            translations['language_selector'],
            options=list(language_options.keys()),
            index=0 if lang == 'en' else 1
        )
        # Update language in session state when changed
        if language_options[selected_language] != lang:
            st.session_state['language'] = language_options[selected_language]
            st.rerun()
            
        st.divider()  # Add a divider for better visual separation
        
        if st.session_state.get('authentication_status'):
            st.page_link("pages/mainpage.py", label=translations['index'])
            st.page_link("pages/1_🌍_Generative_BI_Playground.py", label=translations['playground'], icon="🌍")
            st.markdown(f":gray[{translations['data_customization']}]",
                        help='Add your own datasources and customize description for LLM to better understand them')
            st.page_link("pages/2_🪙_Data_Connection_Management.py", label=translations['data_connection'], icon="🪙")
            st.page_link("pages/3_🪙_Data_Profile_Management.py", label=translations['data_profile'], icon="🪙")
            st.page_link("pages/4_🪙_Schema_Description_Management.py", label=translations['schema_description'], icon="🪙")
            st.page_link("pages/5_🪙_Prompt_Management.py", label=translations['prompt_management'], icon="🪙")
            st.page_link("pages/11_🪙_Environment_Management.py", label=translations['prompt_environment'], icon="🪙")
            st.markdown(f":gray[{translations['performance_enhancement']}]",
                        help='Optimize your LLM for better performance by adding RAG or agent')
            st.page_link("pages/6_📚_Index_Management.py", label=translations['index_management'], icon="📚")
            st.page_link("pages/7_📚_Entity_Management.py", label=translations['entity_management'], icon="📚")
            st.page_link("pages/8_📚_Agent_Cot_Management.py", label=translations['agent_cot'], icon="📚")
            st.page_link("pages/9_🪙_Model_Management.py", label=translations['model_management'], icon="🪙")
            st.page_link("pages/10_📚_User_Authorization.py", label=translations['user_authorization'], icon="📚")

            if st.button(translations['logout']):
                logout()

        elif get_current_page_name() != "Index":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("Index.py")


def logout():
    authenticator = get_authenticator()
    authenticator.logout('Logout', 'unrendered')
    # Get current language
    lang = st.session_state.get('language', 'en')
    if lang == 'en':
        st.info("Logged out successfully!")
    else:
        st.info("成功退出登录！")
    sleep(0.5)
    st.switch_page("Index.py")

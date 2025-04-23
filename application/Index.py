import time
import yaml
from yaml.loader import SafeLoader
import bcrypt

import streamlit as st
from utils.navigation import get_authenticator
from config_files.language_config import get_text

# 必须是第一个Streamlit命令
st.set_page_config(
    page_title="Generative BI",
    page_icon="👋",
)

# Initialize language preference in session state if not already set
if 'language' not in st.session_state:
    st.session_state['language'] = 'en'

# Add language selector
language_options = {'English': 'en', '中文': 'zh'}
selected_language = st.selectbox(
    "Language / 语言",
    options=list(language_options.keys()),
    index=0 if st.session_state['language'] == 'en' else 1
)
# Update language in session state when changed
if language_options[selected_language] != st.session_state['language']:
    st.session_state['language'] = language_options[selected_language]
    st.rerun()

# Get current language
lang = st.session_state['language']

# Load config for authentication
with open('config_files/stauth_config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Display custom login form with translated text
st.header(get_text('login_title', lang))

# Create a form for login
with st.form("login_form"):
    username = st.text_input(get_text('username', lang))
    password = st.text_input(get_text('password', lang), type="password")
    submit_button = st.form_submit_button(get_text('login_button', lang))

# Function to verify password with bcrypt
def verify_password(stored_password, provided_password):
    try:
        # Convert stored password from string to bytes
        stored_password_bytes = stored_password.encode('utf-8')
        # Convert provided password from string to bytes
        provided_password_bytes = provided_password.encode('utf-8')
        # Use bcrypt to check if the passwords match
        return bcrypt.checkpw(provided_password_bytes, stored_password_bytes)
    except Exception as e:
        st.error(f"Error verifying password: {e}")
        return False

# Handle form submission
if submit_button:
    # Check credentials directly from config
    if username in config['credentials']['usernames']:
        stored_password = config['credentials']['usernames'][username]['password']
        
        if verify_password(stored_password, password):
            # Set session state
            st.session_state['authentication_status'] = True
            st.session_state['auth_username'] = username
            st.session_state['auth_name'] = config['credentials']['usernames'][username]['name']
            
            # Set cookie (optional, for compatibility with other pages)
            cookie_name = config['cookie']['name']
            cookie_key = config['cookie']['key']
            cookie_expiry_days = config['cookie']['expiry_days']
            
            st.session_state['cookie_name'] = cookie_name
            st.session_state['cookie_key'] = cookie_key
            st.session_state['cookie_expiry_days'] = cookie_expiry_days
            
            # Redirect to main page
            time.sleep(0.5)
            st.switch_page("pages/mainpage.py")
        else:
            st.error(get_text('login_error', lang))
    else:
        st.error(get_text('login_error', lang))

# Show warning if no form submission yet
if 'authentication_status' not in st.session_state:
    st.warning(get_text('login_warning', lang))

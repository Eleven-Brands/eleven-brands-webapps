import streamlit as st
from shared.shared_auth import require_login, show_user_sidebar


st.set_page_config(page_title="Product Model - Home", layout="wide")

user = require_login()
show_user_sidebar(user)
"""
shared_auth.py

Authentication utilities for Streamlit product catalog app.

This module provides functions to enforce user login before rendering
pages and to display a sidebar UI with user info and logout functionality.
"""

import streamlit as st


def require_login():
     """
     Ensure the user is authenticated before proceeding.

     Checks Streamlit's `st.experimental_user`. If no user is logged in,
     displays a login prompt and halts further execution.

     Returns:
          The authenticated user object from `st.experimental_user`.

     Raises:
          StreamlitStopException: Halts the script when user is not logged in.
     """

     user = st.experimental_user
     if user is None or not user.is_logged_in:
          st.title("🔒 Please Authenticate")
          if st.button("Authenticate"):
               st.login("google")
          st.stop()
     return user


def show_user_sidebar(user, avatar_width: int = 25):
     """
     Render the logged-in user's avatar and name in the sidebar with logout.

     Args:
          user: The authenticated user object (must have `name` and `picture`).
          avatar_width: Width of the avatar image in pixels (default: 25).

     Returns:
          None. Renders HTML and a logout button to the sidebar.
     """

     user_name = user.name.replace(" - Eleven Brands", "")

     with st.sidebar:
          img_html = f'''
               <div 
                    style=" 
                         display: flex; 
                         align-items: center; 
                         gap: 8px; 
                         width: 100%; 
                         margin-bottom: 6px; 
                    ">
                    <img
                         src="{user.picture}"
                         title="{user_name}"
                         width="{avatar_width}"
                         style="border-radius:50%;"
                    />
                    <span style="font-weight:500;">{user_name}</span>
               </div>
          '''
          st.html(img_html)


          if st.button("🚪 Log out"):
               st.logout() 
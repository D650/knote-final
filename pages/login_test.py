import streamlit as st
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
import json
import secrets
import os
oauth = __import__("streamlit-google-oauth")

login_info = oauth.login(
        client_id=json.loads(st.secrets["logintextkey"])["web"]["client_id"],
        client_secret=json.loads(st.secrets["logintextkey"])["web"]["client_secret"],
        redirect_uri=json.loads(st.secrets["logintextkey"])["web"]["redirect_uri"],
        login_button_text="Continue with Google",
        logout_button_text="Logout",
        app_name="Knote",
        app_desc="An AI-Based Study Assistant",
    )

if login_info:
        user_id, user_email = login_info
        st.write(f"Welcome {user_email}")
else:
        st.write("Please login")
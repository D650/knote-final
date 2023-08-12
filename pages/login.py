import streamlit as st
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
import json

flow = Flow.from_client_config(
    json.loads(st.secrets["logintextkey"]),
    scopes=["www.googleapis.com/auth/userinfo.profile", "www.googleapis.com/auth/userinfo.email"],
    redirect_uri= st.secrets["ouath_redirect_url"],
)

# Check if user is already authenticated
if "credentials" not in st.session_state:
    # Generate authorization URL
    authorization_url, _ = flow.authorization_url(prompt='consent')

    # Redirect user to Google's OAuth page for authentication
    st.write(f"Click [here]({authorization_url}) to authenticate with Google.")

# Handle the callback with the authentication code
if "code" in st.experimental_get_query_params():
    auth_code = st.experimental_get_query_params()["code"][0]
    flow.fetch_token(authorization_response=auth_code)
    st.session_state.credentials = flow.credentials

# Use authenticated credentials
if "credentials" in st.session_state:
    credentials = st.session_state.credentials
    service = googleapiclient.discovery.build('plus', 'v1', credentials=credentials)
    user_info = service.people().get(userId='me').execute()

    st.write("Authenticated User's Email:", user_info['emails'][0]['value'])
    st.write("Authenticated User's ID:", user_info['id'])

    # Add a button to display user info
    if st.button("Show User Info"):
        st.write("Authenticated User's Email:", user_info['emails'][0]['value'])
        st.write("Authenticated User's ID:", user_info['id'])

# from googleapiclient.discovery import build
#
# service = build('plus', 'v1', credentials=credentials)
# user_info = service.people().get(userId='me').execute()
# st.write("Authenticated User's Email:", user_info['emails'][0]['value'])
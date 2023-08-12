import streamlit as st
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery
import json


flow = Flow.from_client_config(
    json.loads(st.secrets["logintextkey"]),
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
    redirect_uri= st.secrets["ouath_redirect_url"],
)


if "credentials" not in st.session_state:

    authorization_url, _ = flow.authorization_url(prompt='consent')

    st.write(f"Click [here]({authorization_url}) to authenticate with Google.")


if "code" in st.experimental_get_query_params():
    auth_code = st.experimental_get_query_params()["code"][0]
    flow.fetch_token(authorization_response=auth_code)
    st.session_state.credentials = flow.credentials


if "credentials" in st.session_state:
    credentials = flow.credentials
    service = googleapiclient.discovery.build('plus', 'v1', credentials=credentials)
    user_info = service.people().get(userId='me').execute()

    st.write("Authenticated User's Email:", user_info['emails'][0]['value'])
    st.write("Authenticated User's ID:", user_info['id'])

    if st.button("Show User Info"):
        st.write("Authenticated User's Email:", user_info['emails'][0]['value'])
        st.write("Authenticated User's ID:", user_info['id'])

# from googleapiclient.discovery import build
#
# service = build('plus', 'v1', credentials=credentials)
# user_info = service.people().get(userId='me').execute()
# st.write("Authenticated User's Email:", user_info['emails'][0]['value'])
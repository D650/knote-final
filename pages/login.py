import streamlit as st
import json
from streamlit_oauth import *
import requests

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REFRESH_TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
CLIENT_ID = json.loads(st.secrets["logintextkey"])['web']['client_id']
CLIENT_SECRET = json.loads(st.secrets["logintextkey"])['web']['client_secret']
REDIRECT_URI = json.loads(st.secrets["logintextkey"])['web']['redirect_uris'][0]
SCOPE = "openid profile email"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)

st.title("Login")
st.divider()

if 'token' not in st.session_state:
        st.write("No token in session state. Please authorize below.")
        result = oauth2.authorize_button("🔗 Login with Google", REDIRECT_URI, SCOPE)
        if result:
                st.write("Got token!")
                st.session_state.token = result.get('token')
                st.experimental_rerun()
else:

        token = st.session_state['token']
        # st.json(token)

        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {token["access_token"]}'}
        response = requests.get(user_info_url, headers=headers)
        user_info = response.json()

        st.write(f"Token detected, welcome {user_info['email']}")

        if st.button("♻️ Refresh Token"):
                token = oauth2.refresh_token(token)
        st.session_state.token = token
        # st.experimental_rerun()
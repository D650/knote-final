import firebase_admin
from firebase_admin import credentials, auth, db
import streamlit as st
import json
import firebase_admin.auth
import requests

# # Load Firebase service account key from Streamlit secrets
# firebase_secrets = json.loads(st.secrets["firebase_secrets"])
#
# # Initialize Firebase using the service account key
# cred = credentials.Certificate(firebase_secrets)
# firebase_admin.initialize_app(cred, {
#     'databaseURL': 'YOUR_DATABASE_URL'
# })

def translate_firebase_error(response_json):
    error_message = response_json.get("error", {}).get("message", "Unknown error")
    if "WEAK_PASSWORD" in error_message:
        return "Your password should be at least 6 characters."
    elif "EMAIL_EXISTS" in error_message:
        return "Email address is already in use."
    elif "INVALID_EMAIL" in error_message:
        return "That is an invalid email address."
    elif "MISSING_EMAIL" in error_message:
        return "You did not provide an email address."
    else:
        return error_message

key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred)
else:
    app = firebase_admin._apps


firebase_auth = auth
firebase_database = db

email = st.text_input("Email")
password = st.text_input("Password", type="password")
if st.button("✔️ Login"):
    # Authenticate user using Firebase REST API
    auth_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={st.secrets['firebase_api_key']}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(auth_endpoint, json=payload)

    if response.status_code == 200:
        auth_data = response.json()
        # st.write("Logged in")
        # st.write("User ID:", auth_data["localId"])
        # st.write("ID Token:", auth_data["idToken"])
        # st.json(auth_data)
        st.success(f"Welcome {auth_data['email']}!")
        st.session_state.token = auth_data['idToken']
    else:
        # st.error("Failed to log in. Please check your login credentials and try again.")
        # st.error("Response:", response.text)
        st.error(translate_firebase_error(response.json()))



if st.button("✉️ Forgot Password"):
    # Send password reset email using Firebase REST API
    reset_password_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={st.secrets['firebase_api_key']}"
    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }
    response = requests.post(reset_password_endpoint, json=payload)

    if response.status_code == 200:
        st.success("Password reset email sent. Check your inbox and spam folder.")
    else:
        # st.write("Failed to send password reset email. Please ensure you have entered a valid email.")
        st.error(translate_firebase_error(response.json()))


if st.button("👥 Create Account"):
    # Create new user account using Firebase REST API
    create_account_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={st.secrets['firebase_api_key']}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(create_account_endpoint, json=payload)

    if response.status_code == 200:
        auth_data = response.json()
        st.success(f"Account created and logged in. Welcome {auth_data['email']}")
        st.session_state.token = auth_data['idToken']
        # st.write("User ID:", auth_data["localId"])
        # st.write("ID Token:", auth_data["idToken"])
    else:
        # st.error("Failed to create account")
        st.error(translate_firebase_error(response.json()))
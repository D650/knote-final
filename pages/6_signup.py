import firebase_admin
from firebase_admin import credentials, auth, db
import streamlit as st
import json
import firebase_admin.auth
import requests
import streamlit_extras
from streamlit_extras.row import row
from streamlit_extras.switch_page_button import switch_page

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
        return "That is an invalid email address, or you did not fill out the field"
    elif "INVALID_PASSWORD" in error_message:
        return "That is an incorrect password, or you did not fill out the field"
    elif "MISSING_EMAIL" in error_message:
        return "You did not provide an email address."
    elif "MISSING_PASSWORD" in error_message:
        return "You did not provide a password."
    elif "EMAIL_NOT_FOUND" in error_message:
        return "That account does not exist. Please create an account instead of logging in."
    else:
        return "We ran into an error. Please try again."

key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred)
else:
    app = firebase_admin._apps


firebase_auth = auth
firebase_database = db


if 'token' not in st.session_state:
    st.title("👥 Sign Up")
    st.info("Welcome to Knote, an AI-based study tool. Sign up for an account below. NOTE: It is highly recommended to use Knote on a computer, as some functionality has been found to be unpredictable on mobile.")
    st.divider()

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password2 = st.text_input("Confirm Password", type="password")
    st.divider()

    row = row(2, vertical_align="top", gap="small")


    if row.button("✔️ Submit", use_container_width=True):
        if password == password2:
            create_account_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={st.secrets['firebase_api_key']}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(create_account_endpoint, json=payload)

            if response.status_code == 200:
                auth_data = response.json()
                st.json(auth_data)
                st.balloons()
                st.success(f"Account created and logged in. Welcome {auth_data['email']}!")
                st.session_state.token = auth_data['idToken']
                st.session_state.user_email = auth_data['email']
                st.session_state.user_id = auth_data['localId']
                # st.write("User ID:", auth_data["localId"])
                # st.write("ID Token:", auth_data["idToken"])
            else:
                # st.error("Failed to create account")
                st.error(translate_firebase_error(response.json()))
        else:
            st.error("Those passwords do not match. Please double check and try again.")

    if row.button("👤 Login", use_container_width=True):
        switch_page("login")

else:
    user_info_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={st.secrets['firebase_api_key']}"
    payload = {
        "idToken": st.session_state['token']
    }
    response = requests.post(user_info_endpoint, json=payload)

    if response.status_code == 200:
        user_data = response.json().get("users", [])[0]

        user = user_data['email']
    st.title("👥 Sign Up")
    st.write(f"{user}, you're already logged in.")


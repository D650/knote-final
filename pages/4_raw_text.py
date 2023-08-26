import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import time
import json

import requests
from streamlit_extras.switch_page_button import switch_page

bucket_name = (st.secrets["bucket_name"])


key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name,
        'databaseURL': st.secrets["database_url"]
    })
else:
    app = firebase_admin._apps

def string_to_txt_file(contents, file_name, user):
    storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(f"users/{user}/knote_info/{file_name}.txt")
    blob.upload_from_string(contents)



if 'token' not in st.session_state:
    st.title("🅰 Raw Text")
    st.write("Please login or create an account to access this page.")

    if st.button("Go to login page"):
        switch_page("login")
    if st.button("Go to signup page"):
        switch_page("signup")
else:
    user = st.session_state['user_email']
    st.sidebar.write(f"Hello, {user}!")

    st.title("🅰 Raw Text")
    st.divider()
    st.write("Paste raw text here to convert it into a file to send to the chatbot.")
    user_text = st.text_area(
    "Insert text below",
    value="",height=500)
    if st.button("🤖 Send to File Explorer"):
        string_to_txt_file(user_text,f"text_{int(time.time())}", user)



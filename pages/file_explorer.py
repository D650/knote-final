import os
import streamlit as st
import time
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
import re
import json
from streamlit_oauth import *
import requests
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.row import row

bucket_name = (st.secrets["bucket_name"])

key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name
    })
else:
    app = firebase_admin._apps

def upload_file_to_storage(file, blob_name):
    storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(blob_name)
    blob.upload_from_string(file.read())


def sanitize_filename(filename):
    sanitized_name = filename.rsplit('.', 1)[0]
    return "".join(c for c in sanitized_name if c.isalnum() or c in ["_", "-"])



def delete_file_from_storage(file_path):
    try:
        storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
        bucket = storage_client.bucket("knote-c1512.appspot.com")
        blob = bucket.blob(file_path)
        blob.delete()
    except Exception as e:
        st.error(f"Error deleting file: {e}")

def list_files_in_directory(directory_path, user):
    storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
    bucket = storage_client.bucket("knote-c1512.appspot.com")
    blobs = bucket.list_blobs(prefix=directory_path)
    file_paths = ["/".join((blob.name.split("/")[1:])) for blob in blobs]

    try:
        file_paths.remove(f"users/{user}/knote_info/")
    except ValueError:
        pass

    return file_paths

def clear_dir(directory_path):
    directory_path = f"users/{directory_path}"
    files = list_files_in_directory(directory_path, user)

    if files:
        for file in files:
            delete_file_from_storage(f"users/{file}")
    st.success(f"Directory cleared successfully.")


if 'token' not in st.session_state:
        st.write("No token in session state. Please authorize on the login page.")

        if st.button("Go to login page"):
            switch_page("login")
else:
    user = st.session_state['user_email']
    st.sidebar.write(f"Hello, {user}!")

    st.title("File Explorer")

    st.divider()

    files = list_files_in_directory(f"users/{user}/knote_info", user)
    st.write("Files in the directory:")

    if files:
        st.write(files)
    else:
        st.error("No files found. Go upload some!")

    del_file = st.text_input("Enter the file path to delete:")
    del_file = f"users/{del_file}"

    st.divider()

    row = row(3, vertical_align="top", gap="small")

    if row.button("❌ Delete",use_container_width=True):
        pattern = re.compile(f'^users/{re.escape(user)}/')
        if files and pattern.match(del_file):
            delete_file_from_storage(del_file)
            st.success(f"File deleted.")
        elif not pattern.match(del_file):
            st.error("That file path does not exist.")
        else:
            st.error("File not found.")

    if row.button("🗑️ Delete All Files",use_container_width=True):
        clear_dir(f"{user}/knote_info")

    if row.button("🔄 Refresh",use_container_width=True):
        time.sleep(1)
        st.experimental_rerun()

    st.divider()

    uploaded_files = st.file_uploader("Upload your notes here as txt files.", type=["txt"], accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_extension = os.path.splitext(file_name)[1]

            unique_filename = f"{sanitize_filename(file_name)}_{int(time.time())}{file_extension}"

            upload_file_to_storage(uploaded_file, f"users/{user}/knote_info/{unique_filename}")

        st.success(f"{len(uploaded_files)} file(s) uploaded and saved")
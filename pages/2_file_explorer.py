import os
import streamlit as st
import time
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
import re
import json
import PyPDF2

import requests
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.row import row

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

### PDF PROCESSING FUNCTIONS ####
def string_to_txt_file(contents, file_name, user):
    storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(f"users/{user}/knote_info/{file_name}.txt")
    blob.upload_from_string(contents)

def pdf_to_text(file):
    pdf = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        text += page.extract_text() + "\n"
    return text

def process_uploaded_file(uploaded_file, user):
    file_name = uploaded_file.name
    file_extension = os.path.splitext(file_name)[1]
    if uploaded_file.type == 'application/pdf':
        extracted_text = pdf_to_text(uploaded_file)
    # elif uploaded_file.type.startswith('image/'):
    #     # Convert the image data to a NumPy array (assuming it's in bytes format)
    #     image_data = uploaded_file.read()
    #     np_arr = np.frombuffer(image_data, np.uint8)
    #
    #     # Load the image using OpenCV
    #     image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    #     extracted_text = ocr_for_text(image)
    else:
        st.warning("Unsupported file type. Please upload a PDF file.")
        extracted_text = ""

    st.subheader("Extracted Text:")

    user_text = st.text_area(
        "If this doesn't look right, you can edit it. Once you're ready, click 'Send to Storage'",
        value=extracted_text, height=500)
    if st.button("🤖 Send to Storage"):
        string_to_txt_file(user_text, f"u{file_name.split('.')[0]}_{int(time.time())}.txt", user)


if 'token' not in st.session_state:
        st.title("📁 File Explorer")
        st.write("Please login or create an account to access this page.")

        if st.button("Go to login page"):
            switch_page("login")
        if st.button("Go to signup page"):
            switch_page("signup")
else:
    user = st.session_state['user_email']
    st.sidebar.write(f"Hello, {user}!")

    st.title("📁 File Explorer")
    st.info("Welcome to the file explorer. Here, you can check the files you've uploaded for the chatbot to access. You can either upload .txt or .pdf files below, or input a youtube video link on the youtube transcript extractor page.")
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

    uploaded_files = st.file_uploader("Upload your notes here as txt files.", type=["pdf","txt"], accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_extension = os.path.splitext(file_name)[1]

            unique_filename = f"{sanitize_filename(file_name)}_{int(time.time())}{file_extension}"
            if file_extension == ".txt":
                upload_file_to_storage(uploaded_file, f"users/{user}/knote_info/{unique_filename}")
                st.success(f"{len(uploaded_files)} file(s) uploaded and saved")
            elif file_extension == ".pdf":
                process_uploaded_file(uploaded_file, user)



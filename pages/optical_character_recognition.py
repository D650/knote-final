import PyPDF2
import numpy as np
import cv2
import pytesseract
import os
import streamlit as st
import time
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import shutil
import json

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

bucket_name = (st.secrets["bucket_name"])
user="dsk"


key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name
    })
else:
    app = firebase_admin._apps

def ocr_for_text(image):
    extracted_text = pytesseract.image_to_string(image, lang='eng')
    return extracted_text

def string_to_txt_file(contents, file_name):
    storage_client = storage.Client.from_service_account_json('firebase.json')
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

def process_uploaded_file(uploaded_file):
    file_name = uploaded_file.name
    file_extension = os.path.splitext(file_name)[1]
    if uploaded_file.type == 'application/pdf':
        extracted_text = pdf_to_text(uploaded_file)
    elif uploaded_file.type.startswith('image/'):
        # Convert the image data to a NumPy array (assuming it's in bytes format)
        image_data = uploaded_file.read()
        np_arr = np.frombuffer(image_data, np.uint8)

        # Load the image using OpenCV
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        extracted_text = ocr_for_text(image)
    else:
        st.warning("Unsupported file type. Please upload a PDF or Image file.")
        extracted_text = ""

    st.subheader("Extracted Text:")

    user_text = st.text_area(
        "If this doesn't look right, you can either redo your image, or edit it. Once you're ready, click 'Send to File Explorer', head back to the homepage and ask away!",
        value=extracted_text, height=500)
    if st.button("🤖 Send to File Explorer"):
        string_to_txt_file(user_text, file_name=f"u{file_name.split('.')[0]}_{int(time.time())}.txt")

st.title("Image Saver")

picture = st.camera_input("Take a picture")

if picture is not None:
    os.makedirs("images")
    filename = f"images/{int(time.time())}.jpg"
    with open(filename, "wb") as f:
        f.write(picture.getvalue())

    st.success(f"Image captured and saved as {filename}")

    extracted_text = ocr_for_text(filename)
    st.subheader("Extracted Text:")

    user_text = st.text_area("If this doesn't look right, you can either redo your image, or edit it. Once you're ready, click 'Send to File Explorer', head back to the homepage and ask away!",value=extracted_text,height=500)
    if st.button("🤖 Send to File Explorer"):
        string_to_txt_file(user_text, file_name=f"webcam_{int(time.time())}.txt")
    shutil.rmtree("images")

st.divider()

st.subheader("Webcam not working? Got a screenshot? Upload it here:")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
if uploaded_file is not None:
        process_uploaded_file(uploaded_file)

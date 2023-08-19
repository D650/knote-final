import json
import openai
from langchain import OpenAI
from llama_index import SimpleDirectoryReader, GPTListIndex, GPTVectorStoreIndex, LLMPredictor, PromptHelper, StorageContext, load_index_from_storage
import nltk
import os
import streamlit as st
import time
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
import shutil
import s3fs
from streamlit_oauth import *
import requests

AWS_KEY = st.secrets["aws_key"]
AWS_SECRET = os.environ['aws_secret']
AWS_BUCKET_NAME = os.environ['aws_bucket_name']

assert AWS_KEY is not None and AWS_KEY != ""

s3 = s3fs.S3FileSystem(
    key=AWS_KEY,
    secret=AWS_SECRET,
    client_kwargs={'endpoint_url': 'https://s3.us-east-2.amazonaws.com'},
    s3_additional_kwargs={'ACL': 'public-read'}
)

bucket_name = (st.secrets["bucket_name"])

os.environ["OPENAI_API_KEY"] = (st.secrets["openai_api_key"])
openai_api_key = (st.secrets["openai_api_key"])
openai.api_key = (st.secrets["openai_api_key"])

key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)

if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name
    })
else:
    app = firebase_admin._apps

nltk.download('punkt')

max_input_size = 4096
num_outputs = 512
max_chunk_overlap = 0.5
chunk_size_limit = 600
prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.1, model_name="gpt-3.5-turbo", max_tokens=num_outputs))

if 'token' not in st.session_state:
        st.write("No token in session state. Please authorize on the login page.")
else:

    user_info_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={st.secrets['firebase_api_key']}"
    payload = {
        "idToken": st.session_state['token']
    }
    response = requests.post(user_info_endpoint, json=payload)

    if response.status_code == 200:
        user_data = response.json().get("users", [])[0]

        user = user_data['email']

    def clear_dir(directory_path):

        storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
        bucket = storage_client.bucket("knote-c1512.appspot.com")
        blobs = bucket.list_blobs(prefix=directory_path)
        for blob in blobs:
            blob.delete()

    def tokenize_and_divide(storage_directory, token_limit):
        storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
        bucket = storage_client.bucket(bucket_name)
        clear_dir(f'users/{user}/processed_knote_info')

        processed_dir = f'users/{user}/processed_knote_info'

        blobs = bucket.list_blobs(prefix=storage_directory)

        for blob in blobs:
            if blob.name.endswith(".txt"):
                article_text = blob.download_as_text()
                words = article_text.split()

                chunks = []
                chunk = ""
                for word in words:
                    if len(chunk.split()) + 1 <= token_limit:
                        chunk += word + " "
                    else:
                        chunks.append(chunk.strip())
                        chunk = word + " "
                if chunk:
                    chunks.append(chunk.strip())

                for i, chunk_text in enumerate(chunks):
                    chunk_blob = bucket.blob(f'{processed_dir}/{int(time.time())}.txt')

                    chunk_blob.upload_from_string(chunk_text, content_type='text/plain')
                article_text = None



    def construct_index():
        wait_text = "Please Wait"
        with st.spinner(wait_text):
            storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
            bucket = storage_client.bucket(bucket_name)
            wait_text = "Tokenizing"
            tokenize_and_divide(f"users/{user}/knote_info", 4096)

            local_temp_dir = 'temp_index_processed'
            os.makedirs(local_temp_dir, exist_ok=True)

            blobs = storage_client.list_blobs(bucket_name)

            for blob in blobs:
                try:
                    if blob.name.split("/")[2] == "processed_knote_info" and not blob.name == f"users/{user}/processed_knote_info/" and not blob.name == f"temp_index_processed/":

                        local_file_path = os.path.join(local_temp_dir, os.path.basename(blob.name))
                        blob.download_to_filename(local_file_path)
                except IndexError:
                    pass
                except FileNotFoundError:
                    pass

            max_input_size = 4096
            num_outputs = 512
            max_chunk_overlap = 0.5
            chunk_size_limit = 600
            prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
            llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.1, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
            documents = SimpleDirectoryReader(local_temp_dir).load_data()
            index = GPTVectorStoreIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
            # index_dict = index.storage_context.index_to_json()
            # db.reference('index').set(index_dict)
            shutil.rmtree(local_temp_dir)
            # index.storage_context.persist(f'{user}.json')
            index.storage_context.persist(f'{AWS_BUCKET_NAME}/{user}', fs=s3)
            # local_directory = f"{user}.json"
            # destination_directory = f"users/{user}/{user}.json"
            #
            # for root, _, files in os.walk(local_directory):
            #     for file in files:
            #         local_file_path = os.path.join(root, file)
            #         relative_path = os.path.relpath(local_file_path, local_directory)
            #         destination_blob_name = os.path.join(destination_directory, relative_path).replace("\\", "/")
            #         blob = bucket.blob(destination_blob_name)
            #         blob.upload_from_filename(local_file_path)
            st.success('Index Generated!')
            return index

    def convert_to_dict(vector_store_index):
        serialized_index = vector_store_index.serialize()
        dictionary = json.loads(serialized_index)
        return dictionary

    def chatbot(input_text, messages, uploaded_files=None):
        with st.spinner("Generating response"):
            storage_context = StorageContext.from_defaults(persist_dir=f'{AWS_BUCKET_NAME}/{user}', fs=s3)
            index = load_index_from_storage(storage_context)

            query_engine = index.as_query_engine()

            #If the users last message states '/generatecsv', CSV-formatted pairs with key terms from the files and their definitions, like so 'Term,Definition
            prompt = f"User text: {input_text}\n\nRespond to the users' questions and requests. Please keep responses concise and clear, do not say anything innapropraite or offensive. If user text is '/generatequestions' generate a list of 10 multiple choice questions based on the documents uploaded, be sure to include an answer key at the bottom aswell, also indent each answer choice, DO NOT GENERATE QUESTIONS UNLESS THE USERS LATEST MESSAGES EXPLICITLY STATES '/generatequestions'."
            response = query_engine.query(prompt)

            return response.response


    st.title("📜 Knote Chatbot")
    st.divider()

    st.info("Welcome to the Knowt Chatbot. This chatbot helps you study by answering any questions you have about the information you upload to it. You can also use it to generate questions to aid in your studying. To begin, visit the file explorer page through the sidebar for instruction on how to upload files. Use /generatequestions to generate a list of 10 questions based on your documents.")

    st.info("If you've added or removed any files, please press the button below so I can refresh my memory! (If your folder is empty, and you press the button, my memory won't change.")
    if st.button("Refresh"):
        construct_index()

    st.divider()

    # If there isn't a session variable called messages, create one and add the initial instructions
    # The "messages" session variable will be used to track the entire chat
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Welcome to Knote. Please upload your note files above and ask me anything about them, and I'll answer in a clear and concise manner."}]


    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])


    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        storage_context = StorageContext.from_defaults(persist_dir=f'{AWS_BUCKET_NAME}/{user}', fs=s3)
        index = load_index_from_storage(storage_context)

        response = chatbot(prompt, st.session_state.messages, index)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)




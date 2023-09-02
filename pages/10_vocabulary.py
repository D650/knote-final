import json
import openai
from langchain import OpenAI
from llama_index import SimpleDirectoryReader, GPTListIndex, GPTVectorStoreIndex, LLMPredictor, PromptHelper, StorageContext, load_index_from_storage
# import nltk
import os
import streamlit as st
import time
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
import shutil
import s3fs
import requests
from streamlit_extras.switch_page_button import switch_page
import random
import time
from streamlit_extras.row import row
import csv
import io

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
        'storageBucket': bucket_name,
        'databaseURL': st.secrets["database_url"],
        'name': "knote"
    })
else:
    app = firebase_admin._apps

# nltk.download('punkt')

max_input_size = 4096
num_outputs = 512
max_chunk_overlap = 0.5
chunk_size_limit = 600
prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.1, model_name="gpt-3.5-turbo", max_tokens=num_outputs))

if 'token' not in st.session_state:
    st.title("📚 CSV Vocabulary Generator")
    st.write("Please login or create an account to access this page.")

    if st.button("Go to login page"):
        switch_page("login")
    if st.button("Go to signup page"):
        switch_page("signup")
else:
    user = st.session_state['user_email']
    st.sidebar.write(f"Hello, {user}!")

    def clear_dir(directory_path):

        storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
        bucket = storage_client.bucket("knote-c1512.appspot.com")
        blobs = bucket.list_blobs(prefix=directory_path)
        for blob in blobs:
            blob.delete()


    def vocabbot(number_of_vocab):
        with st.status("Generating Vocabulary CSV...", expanded=True) as status:
            st.write("Accessing Index...")
            try:
                storage_context = StorageContext.from_defaults(persist_dir=f'{AWS_BUCKET_NAME}/{user}', fs=s3)
            except FileNotFoundError:
                st.error("You don't have an index file in storage. Please go to the main page and press 'refresh chatbot' to generate one.")
                st.stop()
            st.write("Index Found!")
            index = load_index_from_storage(storage_context)
            st.write("Querying Chatbot...")
            query_engine = index.as_query_engine()

            #If the users last message states '/generatecsv', CSV-formatted pairs with key terms from the files and their definitions, like so 'Term,Definition
            # prompt = f'User text: {input_text}\n\nGenerate a valid JSON of 10 multiple choice questions with 4 possible answeres based on the information provided in the index. Here is the format:  "question": "What is the capital of France?",  "options": [    "A) London",    "B) Berlin",    "C) Paris",    "D) Madrid"  ],  "correct_answer": "C"'

            prompt = f'Generate a csv of {number_of_vocab} key vocabulary words from the files provided. Here is an example of the format: Cat,A small domesticated carnivorous mammal (Felis catus) known for its affectionate and independent nature. \n\n Dog,A domesticated mammal (Canis lupus familiaris) known for its loyalty diverse breeds and often kept as pets working animals or companions.'


            response = query_engine.query(prompt)
            st.write("Response Generated!")
            vocab_dict = {}

            vocab_list = response.response.split("\n")

            for pair in vocab_list:
                if pair != "":
                    term, definition = pair.split(',', 1)
                    vocab_dict[term.strip()] = definition.strip()

            st.write(vocab_dict)
            st.write("Formatting to CSV...")
            csv_data = ""
            for key in vocab_dict:
                csv_data += f"{key},{dict[key]}\n"

            status.update(label="Vocabulary CSV Generated!", expanded=False)
            return csv_data


    st.title("📚 CSV Vocabulary Generator")
    st.divider()

    st.info("Welcome to the CSV Vocab Generator. You can use this page to extract key vocabulary from the files you've provided, which you can input into a flashcard app like Quizlet or Anki.")
    st.divider()

    row_element = row([4, 1], vertical_align="bottom")
    vocab_num = row_element.slider('How many vocab words would you like to generate?', 1, 75, 25, help="Larger values may lead lower quality vocabulary words near the end")
    vocab_gen_submit = row_element.button("Generate Vocab")

    if vocab_gen_submit:
        csv_data = vocabbot(vocab_num)


        st.download_button(
            "Press to Download",
            csv_data,
            "knote_vocab.csv",
            "text/csv",
            key='download-csv'
        )

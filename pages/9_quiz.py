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
    st.title("📜 Quiz")
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


    def qbot(number_of_q):
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

            prompt = f'Generate a valid JSON of {number_of_q} multiple choice questions with 4 possible answer choices each based on the information provided in the index. Here is the format:  ["question": "What is the capital of France?",  "options": [    "A) London",    "B) Berlin",    "C) Paris",    "D) Madrid"  ]],  "correct_answer": "C) Paris" Generate {number_of_q} of these.'

            response = query_engine.query(prompt)
            st.write("Response Generated!")
            return response.response



    st.title("❓ Quiz Generator")
    st.divider()

    st.info("Welcome to the Quiz Generator. You can use this page to generate a practice test based on the files you provided.")
    st.divider()

    if 'question_dict' not in st.session_state:
        st.session_state.question_dict = None
        st.session_state.questions_loaded = False
        st.session_state.quiz_index = 0
        st.session_state.score = 0
        st.session_state.feedback = []


    def load_questions(number_of_q):
        if not st.session_state.questions_loaded:
            with st.status("Generating Quiz...", expanded=True) as status:
                response = qbot(number_of_q)
                st.session_state.question_dict = json.loads(response)
                random.shuffle(st.session_state.question_dict)
                st.session_state.questions_loaded = True
                status.update(label="Quiz Generated!", expanded=False)


    if st.session_state.question_dict is None:

        row_element = row([4, 1], vertical_align="bottom")
        q_num = row_element.slider('How many questions would you like on the quiz?', 1, 20, 10,
                                       help="Larger values may lead lower quality and repetitive questions.")
        q_gen_submit = row_element.button("Generate Quiz")

        if q_gen_submit:
            load_questions(q_num)

    # Create a dictionary to store selected answers
    selected_answers = {}
    if st.session_state.question_dict:
        with st.form("my_form"):
            if st.session_state.question_dict is not None:
                for index, question in enumerate(st.session_state.question_dict):
                    answer_key = f"answer_{index}"
                    selected_answers[answer_key] = st.selectbox(f"Q{int(index)+1}.{question['question']}", question["options"])


            # Every form must have a submit button.
            submitted = st.form_submit_button()
            if submitted:
                st.session_state.feedback = []
                st.session_state.score = 0
                for index, question in enumerate(st.session_state.question_dict):
                    answer_key = f"answer_{index}"
                    selected_answer = selected_answers[answer_key]
                    if selected_answer == question["correct_answer"]:
                        st.session_state.score += 1
                        st.session_state.feedback.append(f"Q{int(index)+1}: Correct")
                    else:
                        st.session_state.feedback.append(f"Q{int(index) + 1}: Incorrect")
                if st.session_state.score == len(st.session_state.question_dict):
                    st.balloons()
                    st.success("All Correct!")
                else:
                    st.write(st.session_state.feedback)

        # Display the score
        st.metric("Score", f"{st.session_state.score}/{len(st.session_state.question_dict)}")
        reset = st.button("Reset")
        if reset:
            del st.session_state['question_dict']
            st.experimental_rerun()
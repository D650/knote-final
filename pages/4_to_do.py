import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.row import row
from streamlit_extras.stodo import to_do

bucket_name = st.secrets["bucket_name"]
# Initialize Firebase
key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name,
        'databaseURL': st.secrets["database_url"]
    })


# Streamlit app


def add_task(user, task):
    ref = db.reference(f"tasks/{user}")
    new_task_ref = ref.push({"task": task,"completed": False})
    # st.write("Task added with ID:", new_task_ref.key)

def display_tasks(user):
    ref = db.reference(f"tasks/{user}")
    tasks = ref.get()
    if tasks:
        for task_id, task_data in tasks.items():
            if not task_data["completed"]:
                task = to_do(
                    [(st.write, task_data['task'])],
                    task_id,
                )
                if task:
                    ref = db.reference(f"tasks/{user}/{task_id}")
                    ref.delete()
    else:
        st.balloons()
        st.success("Congrats! You have no pending tasks! 😄")

if 'token' not in st.session_state:
    st.title("📜 Knote Chatbot")
    st.write("Please login or create an account to access this page.")

    if st.button("Go to login page"):
        switch_page("login")
    if st.button("Go to signup page"):
        switch_page("signup")
else:
    user_id = st.session_state['user_id']
    user = st.session_state['user_email']
    st.sidebar.write(f"Hello, {user}!")

    st.title("📝 To-Do List")
    st.info("This part of the app doesn't have any AI integration, it's just a helpful to-do list tool.")

    st.divider()


    row_element = row([4, 1], vertical_align="bottom")
    task_input = row_element.text_input("Add a new task:", placeholder="Finish Math Homework", help="Add multiple tasks with comma seperators")
    submit_button = row_element.button("Add Task(s)")

    if submit_button and task_input:
        task_list = task_input.split(",")
        for task in task_list:
            add_task(user_id, task)
            # st.success("Task added!")

    st.write("\nCurrent Tasks:")
    display_tasks(user_id)

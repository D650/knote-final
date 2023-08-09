from youtube_transcript_api import YouTubeTranscriptApi
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import time
import json

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

def string_to_txt_file(contents, file_name):
    storage_client = storage.Client.from_service_account_info(json.loads(st.secrets["textkey"]))
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(f"users/{user}/knote_info/{file_name}.txt")
    blob.upload_from_string(contents)


def get_video_id(youtube_url):
    if "youtube.com/watch?v=" in youtube_url:
        video_id = youtube_url.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video URL.")
    return video_id


def get_transcript(youtube_url):
    try:
        # Get the video ID
        video_id = get_video_id(youtube_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        transcript_text = "\n".join(item['text'] for item in transcript)
        return transcript_text,video_id

    except Exception as e:
        st.error(f"Error: {e}")
        return None


st.title("YouTube Transcript Extractor")
st.write("Enter a YouTube URL to extract its transcript.")

youtube_url = st.text_input("YouTube URL:")
if youtube_url:
    try:
        transcript, video_id = get_transcript(youtube_url)
    except TypeError:
        st.stop()
    if transcript:
        st.write("Transcript:")
        user_text = st.text_area(
            "",
            value=transcript,height=500)
        if st.button("🤖 Send to File Explorer"):
            string_to_txt_file(user_text,f"youtube_{video_id}_{int(time.time())}")



import streamlit as st

st.title("Help Page")
st.markdown(
    """
    **Welcome to the Help Page! Here, you can find information and instructions on how to use our Knote.**

  ## What is Knote?
    Knote is an innovative AI-powered study tool designed to enhance your learning experience. It analyzes documents you provide and generates insightful answers to your questions.
    """
)
st.divider()
st.markdown(
    """
    ## Getting Started
     Using Knote is simple and streamlined, with just three easy steps:
    1. **Upload Information**: Start by navigating to the file explorer page in the sidebar. There, you can effortlessly upload .pdf and .txt files. Alternatively, if you have a YouTube video link, head to the YouTube transcript extractor page and input the video link to extract its transcript.

    2. **Refresh**: After uploading your content, return to the homepage and click the "refresh" button. This ensures that the Knote chabot processes your information for optimal learning outcomes.

    3. **Ask Away**: With your content processed, you're now ready to ask away! Ask questions to the AI chatbot about the files you provided, and it will provide detailed and insightful answers.
    """
)
st.divider()
st.markdown(
"""
    
## Frequently Asked Questions
### Q: What types of documents are supported for upload?
 A: You can upload PDF documents and plain text documents (TXT). The application will extract the content from these files and feed it to the chatbot.

### Q: How accurate is the chatbot in providing answers?
A: The chatbot's accuracy depends on the quality of the content you provide. It uses state-of-the-art natural language processing, but it might not always provide perfect answers. It's recommended to ask clear and concise questions for better results.

### Q: Is there a limit to the length of the content I can input?
A: The application can handle varying lengths of content. However, very long documents might take more time to process. It's recommended to keep the content concise for quicker results.

### Q: Can I interact with the chatbot in a conversational manner?
A: Yes, you can interact with the chatbot in a conversational manner. You can ask follow-up questions based on the chatbot's answers to delve deeper into the topic.

## Contact Us
If you need further assistance or have any questions, please contact our support team at knoteapp0@gmail.com.
"""
)
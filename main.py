
import streamlit as st  # Import Streamlit for building the UI
st.set_page_config(page_title="FIN-RAG", layout="wide")  # Set page title and layout
import base64  # For encoding image files
from pathlib import Path  # For file path management

# Function to set background image
def set_background(image_file):
    image_path = Path(image_file)  # Create a path object from the image path
    if not image_path.exists():  # Check if file exists
        st.error(f"Background image not found: {image_file}")  # Show error if not found
        return

    with open(image_file, "rb") as image:  # Open image in binary mode
        encoded = base64.b64encode(image.read()).decode()  # Encode image to base64
    css = f"""  
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)  # Inject CSS into the Streamlit app

set_background("assets/background2.jpg")  # Call function to set the background

# Import application modules
from chat_storage_mongo import (  # Functions to handle chat storage in MongoDB
    save_chat_message, load_chat_history,
    save_pdf_chat_message, load_pdf_chat_history
)
from streamlit_lottie import st_lottie  # To render Lottie animations
import requests  # For making HTTP requests
from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content  # Scraping utilities
from parse import parse_with_groq  # LLM-based parsing
from pdf_utils import extract_text_from_pdf 
from vectorstore_utils import create_vectorstore_from_text, query_vectorstore  # Vector store for RAG
from auth_utils import create_user_table, add_user, authenticate_user, user_exists  # Authentication utilities
from vectorstore_utils import save_vectorstore, load_vectorstore  # Save/load vector stores
import os  # OS operations
import validators  # For URL validation
from PyPDF2 import PdfReader  # For handling PDF files

# Function to validate URLs
def is_valid_url(url):
    if not validators.url(url):  # Check if URL is properly formatted
        return False
    try:
        response = requests.head(url, timeout=5)  # Make a HEAD request to check reachability
        return response.status_code < 400  # Return True if status is OK
    except requests.RequestException:  # Handle exceptions
        return False

create_user_table()  # Create user table if it doesn't exist

# Handle user login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False  # Initialize login state

# If user not logged in, show login/signup sidebar
if not st.session_state.logged_in:
    st.sidebar.header("🔐 Login")  # Sidebar header
    login_method = st.sidebar.radio("Choose:", ["Login", "Sign Up"]) 

    if login_method == "Sign Up":  # Sign up section
        new_user = st.sidebar.text_input("New Username")  
        new_pass = st.sidebar.text_input("New Password", type="password")  
        if st.sidebar.button("Create Account"):  # Create account button
            if user_exists(new_user):  # Check if user already exists
                st.sidebar.error("Username already exists.")  # Show error
            else:
                add_user(new_user, new_pass)  # Add new user
                st.sidebar.success("User created. Please log in.")  # Show success message

    elif login_method == "Login":  # Login section
        username = st.sidebar.text_input("Username")  
        password = st.sidebar.text_input("Password", type="password") 
        if st.sidebar.button("Login"): 
            if authenticate_user(username, password): 
                st.session_state.logged_in = True  
                st.session_state.username = username  
                st.session_state.chat_history = load_chat_history(username)  # Load chat history
                st.session_state.chat_history_pdf = load_pdf_chat_history(username)  # Load PDF chat history
                st.sidebar.success(f"Welcome {username}!")  # Welcome message
                st.rerun()  # Rerun the app
            else:
                st.sidebar.error("Invalid credentials.")  # Show login error
    st.stop()  # Stop app execution if not logged in

# Function to load Lottie animation from URL
def load_lottie_url(url: str):
    r = requests.get(url)  # Fetch JSON
    if r.status_code != 200:
        return None
    return r.json()  # Return JSON

lottie_animation = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json")  # Load Lottie

# SIDEBAR MENU
with st.sidebar:
    if lottie_animation:
        st_lottie(lottie_animation, height=200, key="sidebar_anim")  # Show Lottie animation

    st.markdown("---")  # Horizontal line
    page = st.radio("Menu", ["🏠 Home", "📝 Summarize", "📄 PDF RAG", "ℹ️ About"])  # Navigation menu

    st.markdown("---")  # Horizontal line
    if st.sidebar.button("🚪 Logout"):  # Logout button
        st.session_state.logged_in = False  # Reset login state
        st.session_state.username = ""  # Clear username
        st.rerun()  # Rerun app

# HOME PAGE
if page == "🏠 Home":
    st.title("AI based FIN-RAG 🧠")  # Page title
    url = st.text_input("Enter a website URL")  # Input field for URL

    if "last_scraped_url" not in st.session_state:
        st.session_state.last_scraped_url = None  # Track previously scraped URL

    if st.button("Scrape Website"):  # Scrape button
        if not is_valid_url(url):  # Validate URL
            st.error("Please enter a valid and reachable URL.")  # Show error
            st.stop()

        if url != st.session_state.last_scraped_url:  # Check for new URL
            st.session_state.chat_history = []  # Reset chat history
            st.session_state.last_scraped_url = url  # Update last scraped URL

        st.write(f"Scraping website: {url}")  # Show scraping status
        result = scrape_website(url)  # Scrape website
        body_content = extract_body_content(result)  # Extract body content
        cleaned_content = clean_body_content(body_content)  # Clean content
        st.session_state.dom_content = cleaned_content  # Save content
        st.session_state.vectorstore = create_vectorstore_from_text(cleaned_content)  # Create vectorstore

        with st.expander("View Scraped Content"):  # Expandable content box
            st.text_area("Content", cleaned_content, height=300)  # Show cleaned content

    if "dom_content" in st.session_state:  # If content exists
        parse_description = st.text_area("Ask what you want to parse?")  # Input parsing question
        if st.button("Parse Content") and parse_description:  # Parse button
            related_docs = query_vectorstore(st.session_state.vectorstore, parse_description)  # Search in vectorstore
            retrieved_text = "\n".join([doc.page_content for doc in related_docs])  # Merge results
            response = parse_with_groq([retrieved_text], parse_description)  # Parse using LLM

            st.session_state.chat_history.append((parse_description, response))  # Save chat
            save_chat_message(st.session_state.username, parse_description, response)  # Save to MongoDB

            st.subheader("Parsed Output")  # Output header
            st.write(response)  # Show result

    if st.session_state.chat_history:  # Show chat history if available
        st.markdown("### Chat History (Last 10 messages)")  # History header
        for q, a in reversed(st.session_state.chat_history[-10:]):  # Loop through history
            st.markdown(f"**You**: {q}")  # Show question
            st.markdown(f"**Bot**: {a}")  # Show answer
    else:
        st.markdown("### Chat History is empty.")  # Message if no history

# SUMMARIZE PAGE
elif page == "📝 Summarize":
    st.title("Summarize Web Content ✨")  # Page title
    if "dom_content" not in st.session_state:
        st.warning("Please scrape a website on the Home page first.")  # Warn if no content
    else:
        if st.button("Generate Summary"):  # Summarize button
            st.write("Summarizing...")  # Show status
            dom_chunks = split_dom_content(st.session_state.dom_content)  # Split content
            summary_prompt = "Summarize the following web content concisely, focusing on main ideas, key data, and insights."  # Prompt
            summary = parse_with_groq(dom_chunks, summary_prompt)  # Get summary from LLM
            st.session_state.summary = summary  # Store summary

            st.subheader("Summary")  # Header
            st.write(summary)  # Show summary

            st.download_button("Download Summary", summary, "summary.txt", "text/plain")  # Download option

# PDF RAG PAGE
elif page == "📄 PDF RAG":
    st.title("PDF-Based Retrieval-Augmented Parsing 📄")  # Page title

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])  # File uploader

    if uploaded_file is not None:
        if not uploaded_file.name.lower().endswith(".pdf"):  # Check if PDF
            st.error("Uploaded file is not a PDF.")
            st.stop()
        try:
            if uploaded_file.size == 0:  # Check for empty file
                st.error("Uploaded PDF is empty.")
                st.stop()

            pdf_text = extract_text_from_pdf(uploaded_file)  # Extract text

            if not pdf_text.strip():  # Check for empty content
                st.error("No text could be extracted from the PDF.")
                st.stop()

            st.session_state.pdf_content = pdf_text  # Store PDF content

            if "pdf_filename" not in st.session_state or st.session_state.pdf_filename != uploaded_file.name:
                st.session_state.vectorstore_pdf = create_vectorstore_from_text(pdf_text)  # Create vectorstore
                st.session_state.chat_history_pdf = load_pdf_chat_history(st.session_state.username)  # Load PDF history
                st.session_state.pdf_filename = uploaded_file.name  # Save filename

            st.subheader("Extracted Content")  # Show content
            st.text_area("PDF Text", pdf_text, height=300)  # Show text area

            query = st.text_area("Ask a question based on the PDF content")  # Ask query

            if st.button("Parse PDF") and query:  # Parse button
                chunks = query_vectorstore(st.session_state.vectorstore_pdf, query)  # Get chunks
                retrieved_text = "\n".join([doc.page_content for doc in chunks])  # Combine
                response = parse_with_groq([retrieved_text], query)  # LLM parsing

                if not response.strip():  # Retry with full content if empty
                    st.info("No answer found in top chunks. Retrying with full document...")
                    full_chunks = split_dom_content(st.session_state.pdf_content)
                    response = parse_with_groq(full_chunks, query)

                st.session_state.chat_history_pdf.append((query, response))  # Save chat
                save_pdf_chat_message(st.session_state.username, query, response)  # Save to MongoDB

                st.subheader("RAG Response")  # Output header
                st.write(response)  # Show response

        except Exception as e:
            st.error(f"Error processing the PDF: {str(e)}")  # Show error
    else:
        st.warning("Please upload a PDF file to proceed.")  # Prompt to upload file

# ABOUT PAGE
elif page == "ℹ️ About":
    st.title("About FIN-RAG")  # Title
    st.markdown("""  # Info about the project
    **FIN-RAG** is a smart AI-powered tool for financial content extraction and summarization.

    **Features**:
    - Web scraping with content cleaning
    - Custom parsing using LLMs
    - Concise summaries with export options

    **Built with**:
    - Streamlit
    - BeautifulSoup + Selenium
    - LangChain + Groq API

    **Owner**:
    - Kavya
    """)

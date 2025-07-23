import streamlit as st
st.set_page_config(page_title="FIN-RAG", layout="wide")
import base64
from pathlib import Path

def set_background(image_file):
    image_path = Path(image_file)
    if not image_path.exists():
        st.error(f"Background image not found: {image_file}")
        return

    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
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
    st.markdown(css, unsafe_allow_html=True)

set_background("assets/background2.jpg")

from chat_storage_mongo import (
    save_chat_message, load_chat_history,
    save_pdf_chat_message, load_pdf_chat_history
)
from streamlit_lottie import st_lottie
import requests
from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_groq
from pdf_utils import extract_text_from_pdf
from vectorstore_utils import create_vectorstore_from_text, query_vectorstore
from auth_utils import create_user_table, add_user, authenticate_user, user_exists

create_user_table()  # ensure user table exists

# AUTHENTICATION
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.header("🔐 Login")
    login_method = st.sidebar.radio("Choose:", ["Login", "Sign Up"])

    if login_method == "Sign Up":
        new_user = st.sidebar.text_input("New Username")
        new_pass = st.sidebar.text_input("New Password", type="password")
        if st.sidebar.button("Create Account"):
            if user_exists(new_user):
                st.sidebar.error("Username already exists.")
            else:
                add_user(new_user, new_pass)
                st.sidebar.success("User created. Please log in.")

    elif login_method == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                # Load persistent chat histories once on login
                st.session_state.chat_history = load_chat_history(username)
                st.session_state.chat_history_pdf = load_pdf_chat_history(username)
                st.sidebar.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials.")
    st.stop()

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_animation = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json")

# SIDEBAR
with st.sidebar:
    if lottie_animation:
        st_lottie(lottie_animation, height=200, key="sidebar_anim")

    st.markdown("---")
    page = st.radio("Menu", ["🏠 Home", "📝 Summarize", "📄 PDF RAG", "ℹ️ About"])

    st.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# HOME PAGE
if page == "🏠 Home":
    st.title("AI based FIN-RAG 🧠")
    url = st.text_input("Enter a website URL")

    if "last_scraped_url" not in st.session_state:
        st.session_state.last_scraped_url = None

    if st.button("Scrape Website"):
        if url != st.session_state.last_scraped_url:
            st.session_state.chat_history = []  # Reset chat history only if URL changed
            st.session_state.last_scraped_url = url

        st.write(f"Scraping website: {url}")
        result = scrape_website(url)
        body_content = extract_body_content(result)
        cleaned_content = clean_body_content(body_content)
        st.session_state.dom_content = cleaned_content
        st.session_state.vectorstore = create_vectorstore_from_text(cleaned_content)

        with st.expander("View Scraped Content"):
            st.text_area("Content", cleaned_content, height=300)

    if "dom_content" in st.session_state:
        parse_description = st.text_area("Ask what you want to parse?")
        if st.button("Parse Content") and parse_description:
            related_docs = query_vectorstore(st.session_state.vectorstore, parse_description)
            retrieved_text = "\n".join([doc.page_content for doc in related_docs])
            response = parse_with_groq([retrieved_text], parse_description)

            st.session_state.chat_history.append((parse_description, response))
            save_chat_message(st.session_state.username, parse_description, response)

            st.subheader("Parsed Output")
            st.write(response)

    # Always visible chat history with last 10 messages or empty message
    if st.session_state.chat_history:
        st.markdown("### Chat History (Last 10 messages)")
        for q, a in reversed(st.session_state.chat_history[-10:]):
            st.markdown(f"**You**: {q}")
            st.markdown(f"**Bot**: {a}")
    else:
        st.markdown("### Chat History is empty.")

# SUMMARIZE PAGE
elif page == "📝 Summarize":
    st.title("Summarize Web Content ✨")
    if "dom_content" not in st.session_state:
        st.warning("Please scrape a website on the Home page first.")
    else:
        if st.button("Generate Summary"):
            st.write("Summarizing...")
            dom_chunks = split_dom_content(st.session_state.dom_content)
            summary_prompt = "Summarize the following web content concisely, focusing on main ideas, key data, and insights."
            summary = parse_with_groq(dom_chunks, summary_prompt)
            st.session_state.summary = summary

            st.subheader("Summary")
            st.write(summary)

            st.download_button("Download Summary", summary, "summary.txt", "text/plain")

# PDF RAG PAGE
elif page == "📄 PDF RAG":
    st.title("PDF-Based Retrieval-Augmented Parsing 📄")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.session_state.pdf_content = pdf_text

        if "pdf_filename" not in st.session_state or st.session_state.pdf_filename != uploaded_file.name:
            st.session_state.vectorstore_pdf = create_vectorstore_from_text(pdf_text)
            st.session_state.chat_history_pdf = load_pdf_chat_history(st.session_state.username)
            st.session_state.pdf_filename = uploaded_file.name

        st.subheader("Extracted Content")
        st.text_area("PDF Text", pdf_text, height=300)

        query = st.text_area("Ask a question based on the PDF content")

        if st.button("Parse PDF") and query:
            chunks = query_vectorstore(st.session_state.vectorstore_pdf, query)
            retrieved_text = "\n".join([doc.page_content for doc in chunks])
            response = parse_with_groq([retrieved_text], query)

            if not response.strip():
                st.info("No answer found in top chunks. Retrying with full document...")
                full_chunks = split_dom_content(st.session_state.pdf_content)
                response = parse_with_groq(full_chunks, query)

            st.session_state.chat_history_pdf.append((query, response))
            save_pdf_chat_message(st.session_state.username, query, response)

            st.subheader("RAG Response")
            st.write(response)

    # Always visible PDF chat history or friendly message
    if st.session_state.chat_history_pdf:
        st.markdown("### PDF RAG Chat History (Last 10 messages)")
        for q, a in reversed(st.session_state.chat_history_pdf[-10:]):
            st.markdown(f"**You**: {q}")
            st.markdown(f"**Bot**: {a}")
    else:
        st.markdown("### PDF RAG Chat History is empty.")

# ABOUT PAGE
elif page == "ℹ️ About":
    st.title("About FIN-RAG")
    st.markdown("""
    **FIN-RAG** is a smart AI-powered tool for financial content extraction and summarization.

    **Features**:
    - Web scraping with content cleaning
    - Custom parsing using LLMs
    - Concise summaries with export options

    **Built with**:
    - Streamlit
    - BeautifulSoup + Selenium
    - LangChain + Groq API
    """)


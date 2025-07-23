#from langchain.vectorstores import FAISS
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


# Initialize embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Split and embed content
def create_vectorstore_from_text(content: str):
    #splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=100)
    texts = splitter.split_text(content)
    documents = [Document(page_content=text) for text in texts]
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

# Perform retrieval
def query_vectorstore(vectorstore, user_query, top_k=5):
    return vectorstore.similarity_search(user_query, k=top_k)

def save_vectorstore(vectorstore, path: str):
    vectorstore.save_local(path)

def load_vectorstore(path: str):
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)



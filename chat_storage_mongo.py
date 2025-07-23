from pymongo import MongoClient
from datetime import datetime

# Connect to local MongoDB server
client = MongoClient("mongodb://localhost:27017/")
#client = MongoClient("mongodb://0.0.0.0:27017/")
db = client["finragdb"]  # Use 'finragdb' as database name
collection = db["chat_history"]  # Collection name stays 'chat_history'

def save_chat_message(username, question, answer):
    doc = {
        "username": username,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)

def load_chat_history(username):
    cursor = collection.find({"username": username}).sort("timestamp", 1)
    chat_history = [(doc["question"], doc["answer"]) for doc in cursor]
    return chat_history

def save_pdf_chat_message(username, question, answer):
    doc = {
        "username": username,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow(),
        "type": "pdf_rag"
    }
    collection.insert_one(doc)

def load_pdf_chat_history(username):
    cursor = collection.find({"username": username, "type": "pdf_rag"}).sort("timestamp", 1)
    chat_history = [(doc["question"], doc["answer"]) for doc in cursor]
    return chat_history


# auth_utils.py

import sqlite3
import hashlib

def create_user_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT
                )''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
              (username, hash_password(password)))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password):
        return True
    return False

def user_exists(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None


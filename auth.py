import sqlite3
import hashlib

class AuthDB:
    def __init__(self):
        self.conn = sqlite3.connect("auth.db")
        self.cur = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password):
        try:
            self.cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                             (username, self.hash_password(password)))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username, password):
        self.cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", 
                         (username, self.hash_password(password)))
        row = self.cur.fetchone()
        return row[0] if row else None

    def close(self):
        self.cur.close()
        self.conn.close()
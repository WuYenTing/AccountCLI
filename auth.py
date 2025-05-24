import sqlite3
import bcrypt

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
        hased = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return hased.decode()
    
    def create_user(self, username, password):
        try:
            self.cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, self.hash_password(password)))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username, password):
        self.cur.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        row = self.cur.fetchone()
        if row:
            user_id, hashed_password = row
            if bcrypt.checkpw(password.encode(), hashed_password.encode()):
                return user_id
        return None

    def close(self):
        self.cur.close()
        self.conn.close()
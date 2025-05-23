import sqlite3
from config import DB_CONFIG  # Expecting something like: {"database": "your_db.sqlite3"}

class DB:
    def __init__(self, db_config):
        self.conn = sqlite3.connect(db_config["database"])
        self.cur = self.conn.cursor()
        self._init_schema()

    def _init_schema(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                date TEXT NOT NULL DEFAULT (DATE('now')),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        self.conn.commit()

    def get_or_create_category(self, full_path):
        self.cur.execute("SELECT id FROM categories WHERE path = ?", (full_path,))
        row = self.cur.fetchone()
        if row:
            return row[0]

        parts = full_path.strip("/").split("/")
        path = ""
        for part in parts:
            path = f"{path}/{part}" if path else part
            self.cur.execute("SELECT id FROM categories WHERE path = ?", (path,))
            if not self.cur.fetchone():
                self.cur.execute("INSERT INTO categories (name, path) VALUES (?, ?)", (part, path))
        self.conn.commit()
        self.cur.execute("SELECT id FROM categories WHERE path = ?", (full_path,))
        return self.cur.fetchone()[0]

    def find_records_by_field(self, field, value):
        if field == "description":
            query = """
                SELECT r.id, c.path, r.description, r.amount, r.date
                FROM records r
                JOIN categories c ON r.category_id = c.id
                WHERE r.description LIKE ?
            """
            params = (f"%{value}%",)

        elif field == "date":
            query = """
                SELECT r.id, c.path, r.description, r.amount, r.date
                FROM records r
                JOIN categories c ON r.category_id = c.id
                WHERE r.date = ?
            """
            params = (value,)

        elif field == "category":
            query = """
                SELECT r.id, c.path, r.description, r.amount, r.date
                FROM records r
                JOIN categories c ON r.category_id = c.id
                WHERE c.path LIKE ?
            """
            # Use `value/%` to include subcategories
            like_value = value if value.endswith('%') else f"{value}%"
            params = (like_value,)

        else:
            raise ValueError("Unsupported field")

        self.cur.execute(query, params)
        return self.cur.fetchall()

    def add_record(self, category_path, description, amount, date=None):
        category_id = self.get_or_create_category(category_path)

        if date:
            self.cur.execute(
                "INSERT INTO records (category_id, description, amount, date) VALUES (?, ?, ?, ?)",
                (category_id, description, amount, date)
            )
        else:
            self.cur.execute(
                "INSERT INTO records (category_id, description, amount) VALUES (?, ?, ?)",
                (category_id, description, amount)
            )

        self.conn.commit()

    def view_records(self):
        self.cur.execute("""
            SELECT r.id, c.path, r.description, r.amount
            FROM records r
            JOIN categories c ON r.category_id = c.id
            ORDER BY r.id
        """)
        return self.cur.fetchall()

    def delete_records_by_category(self, category_path):
        self.cur.execute("SELECT id FROM categories WHERE path LIKE ?", (f"{category_path}%",))
        category_ids = [row[0] for row in self.cur.fetchall()]
        if not category_ids:
            return
        placeholders = ",".join("?" for _ in category_ids)
        self.cur.execute(f"DELETE FROM records WHERE category_id IN ({placeholders})", category_ids)
        self.conn.commit()

    def find_records(self, keyword):
        like_pattern = f"%{keyword}%"
        self.cur.execute("""
            SELECT r.id, c.path, r.description, r.amount
            FROM records r
            JOIN categories c ON r.category_id = c.id
            WHERE c.path LIKE ? OR r.description LIKE ?
        """, (like_pattern, like_pattern))
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()
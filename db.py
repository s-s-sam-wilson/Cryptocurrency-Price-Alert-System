import sqlite3

class Database:

    @staticmethod
    def initdb():
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                rank INTEGER NOT NULL, 
                price_usd REAL NOT NULL,
                market_cap_usd REAL NOT NULL,
                volume_24h_usd REAL NOT NULL,
                timestamp DATETIME NOT NULL
            )
        """)

        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        coin_id TEXT NOT NULL,
                        alert_type TEXT NOT NULL,  -- 'price', 'price_percent', 'volume', 'market_cap'
                        condition TEXT NOT NULL,   -- 'above', 'below'
                        threshold REAL NOT NULL,  
                        percentage REAL,
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_triggered_at DATETIME,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (coin_id) REFERENCES tickers(coin_id)
                    )
                """)
        conn.commit()
        conn.close()
        return conn

    @staticmethod
    def get_connection():
        return sqlite3.connect('app.db', check_same_thread=False)

    @staticmethod
    def insert(table, columns, values):
        conn = Database.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(values))  # e.g., "?, ?, ?"
        query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()
        conn.close()

    @staticmethod
    def select(table, columns, condition=None, params=None, fetch_all=False):
        conn = Database.get_connection()
        cursor = conn.cursor()
        query = f"SELECT {','.join(columns)} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
        conn.close()
        return result

    @staticmethod
    def update(table, columns, values, condition, condition_params):
        conn = Database.get_connection()
        cursor = conn.cursor()
        set_clause = ','.join(f"{col} = ?" for col in columns)
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        cursor.execute(query, values + condition_params)
        conn.commit()
        conn.close()


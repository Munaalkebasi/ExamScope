import os
import sqlite3

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
# Vercel's writable storage is temporary and is suitable only for demo data.
DB_DIR = '/tmp/examscope' if os.environ.get('VERCEL') == '1' else SCHEMA_DIR
DB_PATH = os.path.join(DB_DIR, 'examscope.db')
SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'schema.sql')

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    
    # Initialize settings row if not exists
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM settings WHERE id = 1;")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (id, theme, active_exam_id) VALUES (1, 'dark', NULL);")
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    if one:
        return dict(rv[0]) if rv else None
    return [dict(r) for r in rv]

def execute_db(query, args=()):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    conn.close()
    return cur.lastrowid

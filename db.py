import psycopg2

def get_connection_admin():
    return psycopg2.connect(
        host="192.168.110.111",
        port="55432",
        dbname="ablelink",
        user="admin",
        password="Admin_1234"
    )
    
def get_connection_readonly():
    return psycopg2.connect(
        host="192.168.110.111",
        port="55432",
        dbname="ablelink",
        user="readonly_user",
        password="Readonly_1234"
    )
    
def get_connection_app():
    return psycopg2.connect(
        host="192.168.110.111",
        port="55432",
        dbname="ablelink",
        user="app_user",
        password="App_1234"
    )
    
try:
    conn = get_connection_readonly()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print("✅ Connected successfully!")
    print("📦 PostgreSQL version:", db_version[0])
    cur.close()
    conn.close()
except Exception as e:
    print("❌ Failed to connect:", e)
import psycopg2
from sqlalchemy import create_engine

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
    
    
# def get_connection_readonly():
#     db_url = "postgresql+psycopg2://readonly_user:Readonly_1234@192.168.110.111:55432/ablelink"
#     engine = create_engine(db_url)
#     return engine.connect()


# def get_connection_app():
#     db_url = "postgresql+psycopg2://app_user:App_1234@192.168.110.111:55432/ablelink"
#     engine = create_engine(db_url)
#     return engine.connect()
    
    
if __name__ == "__main__":
    try:
        conn = get_connection_readonly()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print("Connected successfully")
        print("PostgreSQL version: ", db_version[0])
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Failed to connect:", e)
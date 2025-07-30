import psycopg2

def get_connection():
    return psycopg2.connect(
        host="192.168.110.111",
        port="55432",
        dbname="ablelink",
        user="admin",
        password="Admin_1234"
    )

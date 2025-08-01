from sqlalchemy import create_engine
from psycopg2 import OperationalError
from sqlalchemy.exc import DBAPIError, OperationalError



def get_connection_readonly():
    ips = ["192.168.1.111", "192.168.110.111"]
    for ip in ips:
        db_url = f"postgresql+psycopg2://readonly_user:Readonly_1234@{ip}:55432/ablelink"
        try:
            engine = create_engine(db_url, connect_args={"connect_timeout": 3})
            conn = engine.connect()
            print(f"✅ Connected to {ip} (readonly)")
            return conn
        except (OperationalError, DBAPIError) as e:  # ← จับให้กว้างขึ้น
            print(f"❌ Failed to connect to {ip} (readonly): {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error at {ip}: {e}")
            continue
    raise Exception("🚫 All connection attempts failed for readonly_user.")


def get_connection_app():
    ips = ["192.168.1.111", "192.168.110.111"]
    for ip in ips:
        db_url = f"postgresql+psycopg2://app_user:App_1234@{ip}:55432/ablelink"
        try:
            print(f"🔍 Trying {ip} (app)...")
            engine = create_engine(db_url, connect_args={"connect_timeout": 3})
            conn = engine.connect()
            print(f"✅ Connected to {ip} (app)")
            return conn
        except (OperationalError, DBAPIError) as e:
            print(f"❌ Failed to connect to {ip} (app): {type(e).__name__} → {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error at {ip} (app): {type(e).__name__} → {e}")
            continue
    raise Exception("🚫 All connection attempts failed for app_user.")
    
    
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
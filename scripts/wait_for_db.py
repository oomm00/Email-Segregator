"""Wait for PostgreSQL to be ready, then exit."""
import sys
import time

import psycopg2

dsn = sys.argv[1] if len(sys.argv) > 1 else "host=postgres dbname=shipping_email user=shipping password=shipping_secret"

for i in range(30):
    try:
        conn = psycopg2.connect(dsn)
        conn.close()
        print("database ready")
        sys.exit(0)
    except Exception as e:
        print(f"waiting for db ({i+1}/30): {e}")
        time.sleep(1)

print("database not ready after 30s")
sys.exit(1)

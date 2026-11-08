# Backend/init_db.py
"""
Script untuk inisialisasi database.
Jalankan dengan: python init_db.py
"""
import pymysql
from config import DB_CONFIG


def init_database():
    """Buat database dan tables dari schema"""
    
    # Baca SQL schema
    with open("database_schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    
    # Koneksi ke MySQL server (tanpa database)
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG.get("port", 3306),
        autocommit=True
    )
    
    try:
        with conn.cursor() as cur:
            # Buat database jika belum ada
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            print(f"✓ Database '{DB_CONFIG['database']}' created/verified")
            
            # Gunakan database
            cur.execute(f"USE {DB_CONFIG['database']}")
        
        # Buka koneksi baru dengan database yang tepat
        conn.close()
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG.get("port", 3306),
            autocommit=True
        )
        
        # Eksekusi SQL schema
        with conn.cursor() as cur:
            # Split by CREATE TABLE/INDEX statements
            statements = schema.split(";")
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        cur.execute(statement)
                        print(f"✓ {statement[:50]}...")
                    except pymysql.Error as e:
                        if "already exists" in str(e):
                            print(f"⚠ {statement[:50]}... (already exists)")
                        else:
                            print(f"✗ Error: {e}")
        
        print("\n✓ Database initialization completed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_database()

#!/usr/bin/env python3
"""
Script untuk reset database dengan skema terbaru
"""
import pymysql
from config import DB_CONFIG

def reset_database():
    """Reset database dan load skema baru"""
    
    # Connect ke MySQL (tanpa database dulu)
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG.get("port", 3306),
    )
    
    with conn.cursor() as cur:
        # Drop existing database
        print("📌 Dropping existing database...")
        cur.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
        print("✅ Database dropped")
        
        # Create new database
        print("📌 Creating new database...")
        cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        print("✅ Database created")
        
        # Select database
        cur.execute(f"USE {DB_CONFIG['database']}")
        
        # Read dan execute schema file
        print("📌 Loading schema...")
        with open("database_schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()
        
        # Split by semicolon dan execute setiap statement
        statements = [s.strip() for s in schema.split(";") if s.strip()]
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f"⚠️ Error executing statement: {e}")
                print(f"  Statement: {stmt[:100]}...")
        
        print("✅ Schema loaded successfully")
    
    conn.commit()
    conn.close()
    
    print("\n✨ Database reset complete!")
    print("Database ready to use. Upload data dan jalankan preprocessing.")

if __name__ == "__main__":
    reset_database()

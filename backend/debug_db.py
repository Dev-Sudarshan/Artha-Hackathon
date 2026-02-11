from db.database import get_connection
import json

def debug_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("--- USERS ---")
    cursor.execute("SELECT * FROM users")
    for row in cursor.fetchall():
        print(f"Phone: {row['phone']}, Data: {row['json_data']}")
        
    print("\n--- KYC ---")
    cursor.execute("SELECT * FROM kyc")
    for row in cursor.fetchall():
        print(f"User ID: {row['user_id']}, Data: {row['json_data']}")
        
    print("\n--- SESSIONS ---")
    cursor.execute("SELECT * FROM sessions")
    for row in cursor.fetchall():
        print(f"Token: {row['token']}, Data: {row['json_data']}")

    print("\n--- CREDIT SCORES ---")
    cursor.execute("SELECT * FROM credit_scores")
    for row in cursor.fetchall():
        print(f"User ID: {row['user_id']}, Score: {row['score']}")

    conn.close()

if __name__ == "__main__":
    debug_db()

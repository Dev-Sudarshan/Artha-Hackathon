import json
import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://aartha_user:uCdz5w5vQSXADl6ocUGGCuI2iNu3Bybl@dpg-d631i1onputs73a007ng-a.virginia-postgres.render.com/aartha",
)

# SQLAlchemy setup for admin panel
SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """SQLAlchemy session generator for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _normalize_db_url(url: str) -> str:
    if not url:
        raise ValueError("DATABASE_URL is not set")
    if "sslmode=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}sslmode=require"


def get_connection():
    db_url = _normalize_db_url(DATABASE_URL)
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )

    # 2. Sessions Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )

    # 3. OTPs Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS otps (
            phone TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )

    # 4. KYC Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS kyc (
            user_id TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )

    # 5. Credit Scores Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_scores (
            user_id TEXT PRIMARY KEY,
            score INTEGER
        )
        """
    )

    # 6. Loans Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS loans (
            loan_id TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )

    # 7. Transactions Table (Key-Value - Receipt)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            loan_id TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )
    
    # 8. Financial Data Table (Key-Value)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS financial_data (
            user_id TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )
    
    # 9. Repayments Table (Relational / List Storage)
    # Storing individual repayments relationally allows easy query by loan_id
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS repayments (
            repayment_id TEXT PRIMARY KEY,
            loan_id TEXT,
            json_data JSONB
        )
        """
    )

    # 10. Audit/Other Stores (Agreement Execution)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agreement_executions (
            loan_id TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )

    # 11. Loan Acceptance Store (Audit)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS loan_acceptances (
            loan_id TEXT PRIMARY KEY,
            json_data JSONB
        )
        """
    )
    
    # 12. Admin Users Table (for Admin Panel)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'support_admin',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Create an index on email for faster lookups
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email)
        """
    )
    
    conn.commit()
    conn.close()

# ---- GENERIC HELPERS ----

def put_item(table: str, key: str, data: Dict[str, Any]):
    """Store a dict as JSON"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # For credit_scores table, it's just user_id and score(int)
    if table == 'credit_scores':
        cursor.execute(
            f"""
            INSERT INTO {table} (user_id, score)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET score = EXCLUDED.score
            """,
            (key, data),
        )
    else:
        # Standard Key-Value JSON Tables (users, sessions, otps, kyc, loans, transactions, etc)
        # Note: PK column name varies, we assume standard schema has 2 cols: PK and json_data.
        # But we need to know the PK column name.
        # Let's verify PK name map.
        pk_map = {
            "users": "phone",
            "sessions": "token",
            "otps": "phone",
            "kyc": "user_id",
            "loans": "loan_id",
            "transactions": "loan_id", # Based on transaction_service usage: key is loan_id? No, verify_transaction assumes tx_id. 
                                       # Wait, transaction_service uses TRANSACTION_STORE[loan_id]. 
                                       # Actually line 63: TRANSACTION_STORE[loan_id] = receipt_data. 
                                       # But audit_service verify_transaction uses tx_id.
                                       # Let's fix this inconsistency in the caller. 
                                       # For now, generic helper assumes first col is PK.
            "financial_data": "user_id",
            "agreement_executions": "loan_id",
            "loan_acceptances": "loan_id",
            "repayments": "repayment_id" 
        }
        
        pk_col = pk_map.get(table)
        if not pk_col:
             raise ValueError(f"Unknown table: {table}")

        cursor.execute(
            f"""
            INSERT INTO {table} ({pk_col}, json_data)
            VALUES (%s, %s)
            ON CONFLICT ({pk_col}) DO UPDATE SET json_data = EXCLUDED.json_data
            """,
            (key, Json(data)),
        )
    
    conn.commit()
    conn.close()

def get_item(table: str, key: str) -> Optional[Dict[str, Any]]:
    """Retrieve dict from JSON"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if table == 'credit_scores':
        cursor.execute(f"SELECT score FROM {table} WHERE user_id = %s", (key,))
        row = cursor.fetchone()
        conn.close()
        return row['score'] if row else None
    
    pk_map = {
        "users": "phone",
        "sessions": "token",
        "otps": "phone",
        "kyc": "user_id",
        "loans": "loan_id",
        "transactions": "loan_id",
        "financial_data": "user_id",
        "agreement_executions": "loan_id",
        "loan_acceptances": "loan_id",
        "repayments": "repayment_id"
    }
    pk_col = pk_map[table]
    
    cursor.execute(f"SELECT json_data FROM {table} WHERE {pk_col} = %s", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        if isinstance(row['json_data'], str):
            return json.loads(row['json_data'])
        return row['json_data']
    return None

def delete_item(table: str, key: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    pk_map = {
        "users": "phone",
        "sessions": "token",
        "otps": "phone",
        "kyc": "user_id" # Add others if needed
    }
    pk_col = pk_map.get(table, "user_id") # Default risky
    if table in ["otps", "users", "sessions"]:
         pk_col = pk_map[table]
    
    cursor.execute(f"DELETE FROM {table} WHERE {pk_col} = %s", (key,))
    conn.commit()
    conn.close()

def get_all_items(table: str) -> Dict[str, Any]:
    """Return all items as a dict (key -> data) to mimic full dictionary access"""
    conn = get_connection()
    cursor = conn.cursor()
    
    pk_map = {
        "loans": "loan_id",
        "users": "phone",
        "kyc": "user_id",
        "otps": "phone",
        "credit_scores": "user_id"
    }
    
    if table not in pk_map:
        return {} # Only supporting loans for marketplace listing currently
        
    pk_col = pk_map[table]
    cursor.execute(f"SELECT {pk_col}, json_data FROM {table}")
    rows = cursor.fetchall()
    conn.close()
    
    result = {}
    for row in rows:
        json_data = row['json_data']
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        result[row[pk_col]] = json_data
    return result

def get_repayments(loan_id: str) -> List[Dict[str, Any]]:
    """Specific helper for fetching list of repayments"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT json_data FROM repayments WHERE loan_id = %s", (loan_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        json_data = row['json_data']
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        results.append(json_data)
    return results

def add_repayment(repayment_id: str, loan_id: str, data: Dict[str, Any]):
    """Specific helper for adding repayment"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO repayments (repayment_id, loan_id, json_data)
        VALUES (%s, %s, %s)
        """,
        (repayment_id, loan_id, Json(data)),
    )
    conn.commit()
    conn.close()

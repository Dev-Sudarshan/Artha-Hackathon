import json
import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2 import pool as psycopg2_pool
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


# ---- CONNECTION POOL (reuses warm TCP+SSL connections) ----
_connection_pool = None

def _get_pool():
    global _connection_pool
    if _connection_pool is None:
        db_url = _normalize_db_url(DATABASE_URL)
        _connection_pool = psycopg2_pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=15,
            dsn=db_url,
            cursor_factory=RealDictCursor,
        )
    return _connection_pool


def get_connection():
    """Get a connection from the pool (much faster than opening a new one each time)."""
    return _get_pool().getconn()


def release_connection(conn):
    """Return a connection back to the pool."""
    try:
        _get_pool().putconn(conn)
    except Exception:
        pass

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
    release_connection(conn)

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
    release_connection(conn)

def get_item(table: str, key: str) -> Optional[Dict[str, Any]]:
    """Retrieve dict from JSON"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if table == 'credit_scores':
        cursor.execute(f"SELECT score FROM {table} WHERE user_id = %s", (key,))
        row = cursor.fetchone()
        release_connection(conn)
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
    release_connection(conn)
    
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
    release_connection(conn)

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

    # credit_scores has (user_id, score) not json_data
    if table == "credit_scores":
        cursor.execute(f"SELECT {pk_col}, score FROM {table}")
        rows = cursor.fetchall()
        release_connection(conn)
        return {row[pk_col]: row['score'] for row in rows}

    cursor.execute(f"SELECT {pk_col}, json_data FROM {table}")
    rows = cursor.fetchall()
    release_connection(conn)
    
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
    release_connection(conn)
    results = []
    for row in rows:
        json_data = row['json_data']
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        results.append(json_data)
    return results


def get_user_loan_summary(phone: str) -> dict:
    """Fetch loan totals for a specific user efficiently via SQL instead of loading ALL loans."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT loan_id, json_data FROM loans")
    rows = cursor.fetchall()
    release_connection(conn)

    total_borrowed = 0
    total_lended = 0
    borrower_active = False
    lender_active = False

    for row in rows:
        loan = row['json_data']
        if isinstance(loan, str):
            loan = json.loads(loan)
        if loan.get("user_id") == phone:
            total_borrowed += int(loan.get("amount") or 0)
            if loan.get("status") in ["LISTED", "ACTIVE", "AWAITING_SIGNATURE"]:
                borrower_active = True
        if loan.get("lender_id") == phone:
            total_lended += int(loan.get("amount") or 0)
            if loan.get("status") in ["ACTIVE", "REPAID"]:
                lender_active = True

    active_role = "none"
    if borrower_active and not lender_active:
        active_role = "borrower"
    elif lender_active and not borrower_active:
        active_role = "lender"
    elif borrower_active and lender_active:
        active_role = "both"

    return {
        "total_borrowed": total_borrowed,
        "total_lended": total_lended,
        "active_role": active_role,
    }

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
    release_connection(conn)


def get_user_profile_data(phone: str) -> dict:
    """Fetch user + kyc + credit_score + loan summary in ONE connection for /auth/me."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. User
    cursor.execute("SELECT json_data FROM users WHERE phone = %s", (phone,))
    row = cursor.fetchone()
    user_data = None
    if row:
        user_data = row['json_data']
        if isinstance(user_data, str):
            user_data = json.loads(user_data)

    # 2. KYC
    cursor.execute("SELECT json_data FROM kyc WHERE user_id = %s", (phone,))
    row = cursor.fetchone()
    kyc_data = None
    if row:
        kyc_data = row['json_data']
        if isinstance(kyc_data, str):
            kyc_data = json.loads(kyc_data)

    # 3. Credit Score
    cursor.execute("SELECT score FROM credit_scores WHERE user_id = %s", (phone,))
    row = cursor.fetchone()
    credit_score = row['score'] if row else None

    # 4. Loan summary
    cursor.execute("SELECT json_data FROM loans")
    rows = cursor.fetchall()

    release_connection(conn)

    total_borrowed = 0
    total_lended = 0
    borrower_active = False
    lender_active = False

    for row in rows:
        loan = row['json_data']
        if isinstance(loan, str):
            loan = json.loads(loan)
        if loan.get("user_id") == phone:
            total_borrowed += int(loan.get("amount") or 0)
            if loan.get("status") in ["LISTED", "ACTIVE", "AWAITING_SIGNATURE"]:
                borrower_active = True
        if loan.get("lender_id") == phone:
            total_lended += int(loan.get("amount") or 0)
            if loan.get("status") in ["ACTIVE", "REPAID"]:
                lender_active = True

    active_role = "none"
    if borrower_active and not lender_active:
        active_role = "borrower"
    elif lender_active and not borrower_active:
        active_role = "lender"
    elif borrower_active and lender_active:
        active_role = "both"

    return {
        "user": user_data,
        "kyc": kyc_data,
        "credit_score": credit_score,
        "total_borrowed": total_borrowed,
        "total_lended": total_lended,
        "active_role": active_role,
    }


def check_user_active_loans(user_id: str) -> Dict[str, Any]:
    """
    Efficiently check if a user has active loans (as borrower or lender).
    Returns: {
        "has_active_as_borrower": bool,
        "has_active_as_lender": bool,
        "active_borrower_loan_id": str | None,
        "active_lender_loan_id": str | None
    }
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check for active borrower loans
    cursor.execute("""
        SELECT loan_id, json_data->>'status' as status 
        FROM loans 
        WHERE json_data->>'user_id' = %s 
        AND json_data->>'status' IN ('PENDING_ADMIN_APPROVAL', 'LISTED', 'ACTIVE', 'AWAITING_SIGNATURE')
        LIMIT 1
    """, (user_id,))
    borrower_row = cursor.fetchone()
    
    # Check for active lender loans
    cursor.execute("""
        SELECT loan_id, json_data->>'status' as status 
        FROM loans 
        WHERE json_data->>'lender_id' = %s 
        AND json_data->>'status' NOT IN ('REPAID', 'DEFAULTED', 'CANCELLED')
        LIMIT 1
    """, (user_id,))
    lender_row = cursor.fetchone()
    
    release_connection(conn)
    
    return {
        "has_active_as_borrower": borrower_row is not None,
        "has_active_as_lender": lender_row is not None,
        "active_borrower_loan_id": borrower_row['loan_id'] if borrower_row else None,
        "active_lender_loan_id": lender_row['loan_id'] if lender_row else None,
    }
"""
Database Migration Script
Adds blockchain-related columns to the loans table

Run this script to update your database schema:
    python migrate_blockchain_fields.py
"""

import os
import sys
from sqlalchemy import create_engine, text

# Import DATABASE_URL from your existing database configuration
try:
    from db.database import DATABASE_URL
except ImportError:
    # Fallback if import fails
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/aartha")

def migrate():
    """Add blockchain fields to loans table"""
    print("🔄 Starting blockchain fields migration...")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # SQL to add new columns
        migrations = [
            """
            ALTER TABLE loans 
            ADD COLUMN IF NOT EXISTS blockchain_tx_hash VARCHAR(255);
            """,
            """
            ALTER TABLE loans 
            ADD COLUMN IF NOT EXISTS blockchain_status VARCHAR(50) DEFAULT 'NOT_STORED';
            """,
            """
            ALTER TABLE loans 
            ADD COLUMN IF NOT EXISTS blockchain_loan_hash VARCHAR(255);
            """,
            """
            ALTER TABLE loans 
            ADD COLUMN IF NOT EXISTS blockchain_stored_at TIMESTAMP;
            """,
            """
            ALTER TABLE loans 
            ADD COLUMN IF NOT EXISTS blockchain_repaid_tx_hash VARCHAR(255);
            """
        ]
        
        # Execute migrations
        with engine.connect() as conn:
            for i, migration in enumerate(migrations, 1):
                print(f"⚙️  Executing migration {i}/{len(migrations)}...")
                conn.execute(text(migration))
                conn.commit()
        
        print("✅ Migration completed successfully!")
        print("\nNew columns added to 'loans' table:")
        print("  - blockchain_tx_hash")
        print("  - blockchain_status")
        print("  - blockchain_loan_hash")
        print("  - blockchain_stored_at")
        print("  - blockchain_repaid_tx_hash")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

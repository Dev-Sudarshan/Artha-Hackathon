"""Script to create initial admin user"""
import os
import sys
import bcrypt

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from db.database import get_connection

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_admin_user(email: str, password: str, role: str = "super_admin"):
    """Create an admin user in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_pw = hash_password(password)
    
    try:
        cursor.execute(
            """
            INSERT INTO admin_users (email, hashed_password, role, is_active)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (email) DO UPDATE 
            SET hashed_password = EXCLUDED.hashed_password,
                role = EXCLUDED.role
            RETURNING id, email, role
            """,
            (email, hashed_pw, role)
        )
        
        result = cursor.fetchone()
        conn.commit()
        
        print(f"✅ Admin user created/updated successfully!")
        print(f"   ID: {result['id']}")
        print(f"   Email: {result['email']}")
        print(f"   Role: {result['role']}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Default admin credentials
    admin_email = os.getenv("ADMIN_EMAIL", "admin@artha.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_role = os.getenv("ADMIN_ROLE", "super_admin")
    
    print(f"Creating admin user: {admin_email}")
    create_admin_user(admin_email, admin_password, admin_role)
    print("\nYou can now login with these credentials at /api/admin/auth/login")

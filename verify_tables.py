"""
Verify that database tables were created successfully.

This script checks if the required tables exist in the database
without requiring psql to be installed.
"""

from __future__ import annotations

from database.postgresql_setup import get_engine
from sqlalchemy import inspect, text


def verify_tables() -> None:
    """Verify that all required tables exist in the database."""
    import os
    
    # Show what credentials are being used
    print("Database connection settings:")
    print(f"  User: {os.environ.get('POSTGRES_USER', 'postgres (default)')}")
    print(f"  Host: {os.environ.get('POSTGRES_HOST', 'localhost (default)')}")
    print(f"  Port: {os.environ.get('POSTGRES_PORT', '5432 (default)')}")
    print(f"  Database: {os.environ.get('POSTGRES_DB', 'planner (default)')}")
    print()
    
    try:
        engine = get_engine()
        
        # Get table inspector
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Required tables
        required_tables = ['test_tasks', 'coverage', 'task_comments']
        
        print("Checking database tables...")
        print(f"Found {len(existing_tables)} table(s) in database")
        print()
        
        all_present = True
        for table in required_tables:
            if table in existing_tables:
                print(f"[OK] Table '{table}' exists")
                
                # Get column info
                columns = inspector.get_columns(table)
                print(f"  Columns: {', '.join([col['name'] for col in columns])}")
            else:
                print(f"[ERROR] Table '{table}' NOT FOUND")
                all_present = False
        
        print()
        
        if all_present:
            print("[OK] All required tables are present!")
            
            # Check enum types
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT typname FROM pg_type 
                    WHERE typname IN ('test_type_enum', 'task_status_enum', 'coverage_status_enum')
                    ORDER BY typname
                """))
                enum_types = [row[0] for row in result]
                
                if enum_types:
                    print(f"[OK] Found enum types: {', '.join(enum_types)}")
                else:
                    print("[WARNING] No enum types found (they may have been created with different names)")
        else:
            print("[ERROR] Some required tables are missing!")
            print("  Run 'python create_tables.py' to create them.")
            
    except Exception as e:
        print(f"[ERROR] Error connecting to database: {e}")
        print()
        print("Please check:")
        print("  1. PostgreSQL is running")
        print("  2. Environment variables are set correctly")
        print("  3. Database exists")
        print("  4. Credentials are correct")


if __name__ == "__main__":
    verify_tables()


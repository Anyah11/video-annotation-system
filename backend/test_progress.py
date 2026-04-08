from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://localhost/video_annotation_db"

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()
        print("✅ PostgreSQL Connection Successful!")
        print(f"📊 PostgreSQL Version: {version[0]}")
        
        # Test creating a table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS test_python (
                id SERIAL PRIMARY KEY,
                message TEXT
            );
        """))
        connection.commit()
        
        # Insert data
        connection.execute(text("""
            INSERT INTO test_python (message) VALUES ('Hello from Python!');
        """))
        connection.commit()
        
        # Query data
        result = connection.execute(text("SELECT * FROM test_python;"))
        rows = result.fetchall()
        print(f"✅ Python can write to database! Rows: {len(rows)}")
        
        # Clean up
        connection.execute(text("DROP TABLE test_python;"))
        connection.commit()
        
        print("✅ All tests passed! PostgreSQL is ready to use!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("1. PostgreSQL is running: brew services start postgresql@14")
    print("2. Database exists: createdb video_annotation_db")
    print("3. Python packages installed: pip install sqlalchemy psycopg2-binary")
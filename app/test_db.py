from sqlalchemy import text

from app.config.database import engine


try:
    with engine.connect() as connection:

        database = connection.execute(
            text("SELECT current_database();")
        ).scalar()

        tables = connection.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
        ).fetchall()

        print("Connected database:", database)

        print("Tables:")
        for table in tables:
            print("-", table[0])

except Exception as e:
    print("Database connection failed!")
    print(e)
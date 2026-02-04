from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
server = os.getenv("POSTGRES_SERVER", "localhost")
port = os.getenv("POSTGRES_PORT", "5435")
db_name = os.getenv("POSTGRES_DB", "openvoice")

url = f"postgresql://{user}:{password}@{server}:{port}/{db_name}"
engine = create_engine(url)

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS description VARCHAR"))
        conn.commit()
    print("Schema updated successfully")
except Exception as e:
    print(f"Error updating schema: {e}")

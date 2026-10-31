import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Load .env from the project root
project_root = Path(__file__).resolve().parent
load_dotenv(project_root / ".env")

# Read settings without printing private credentials
uri = os.getenv("MONGODB_URI")
database_name = os.getenv("MONGODB_DATABASE", "metaclean")

if not uri or "YOUR_CLUSTER_ADDRESS" in uri:
    raise RuntimeError(
        "MONGODB_URI is missing or still contains the example placeholder."
    )

client = MongoClient(
    uri,
    serverSelectionTimeoutMS=10000,
)

try:
    # Send a real request to confirm connectivity
    client.admin.command("ping")
    print("SUCCESS: Connected to MongoDB Atlas!")

    # Select the MetaClean database
    db = client[database_name]

    # List existing collections
    collections = db.list_collection_names()
    print(f"Database selected: {database_name}")
    print("Collections:", collections)

except PyMongoError as error:
    print("MongoDB connection failed.")
    print("Error type:", type(error).__name__)
    print("Details:", str(error))

finally:
    client.close()
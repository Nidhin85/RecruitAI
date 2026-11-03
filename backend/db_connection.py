
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# Load settings from the backend .env file.
BACKEND_FOLDER = Path(__file__).resolve().parent
load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017/"
)

DATABASE_NAME = "recruitment_system"


def test_connection():
    client = None

    try:
        # Create a connection to MongoDB.
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )

        # Check whether MongoDB responds.
        client.admin.command("ping")

        # Select our project database.
        database = client[DATABASE_NAME]

        print("MongoDB connection successful!")
        print("Database:", DATABASE_NAME)

        # Collections are created when data is inserted.
        print("Candidate collection:", "candidates")
        print("Job collection:", "jobs")

        return database

    except PyMongoError as error:
        print("MongoDB connection failed.")
        print("Check that MongoDB is installed and running.")
        print("Technical details:", error)
        return None

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    test_connection()

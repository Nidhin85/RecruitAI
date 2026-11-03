
from pathlib import Path
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


BACKEND_FOLDER = Path(__file__).resolve().parent
load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017/"
)

DATABASE_NAME = "recruitment_system"
COLLECTION_NAME = "candidates"


def main():
    client = None

    try:
        # Connect to the database.
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        database = client[DATABASE_NAME]
        collection = database[COLLECTION_NAME]

        # Count saved candidate records.
        total = collection.count_documents({})

        print("===== CANDIDATES FROM MONGODB =====")
        print("Total candidate records:", total)

        # Retrieve candidate details.
        candidates = collection.find(
            {},
            {
                "_id": 0,
                "name": 1,
                "email": 1,
                "phone": 1,
                "skills": 1,
                "education": 1,
                "source_file": 1,
                "needs_recruiter_review": 1
            }
        ).sort("name", 1)

        for number, candidate in enumerate(candidates, start=1):
            print(f"\nCandidate {number}")
            print("Name:", candidate.get("name") or "Not available")
            print("Email:", candidate.get("email") or "Not available")
            print("Phone:", candidate.get("phone") or "Not available")
            print("Skills:", candidate.get("skills", []))
            print("Education:", candidate.get("education", []))
            print("Source PDF:", candidate.get("source_file"))
            print(
                "Needs review:",
                candidate.get("needs_recruiter_review", True)
            )

        if total == 0:
            print("No records found. Run candidate_store.py first.")

    except PyMongoError as error:
        print("Could not retrieve candidate records.")
        print("Error:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

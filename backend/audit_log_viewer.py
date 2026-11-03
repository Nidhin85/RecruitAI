
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


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME]["audit_logs"]
        records = list(
            collection.find({}).sort("timestamp", -1).limit(50)
        )

        if not records:
            print("No audit events found.")
            return

        print("===== AUDIT HISTORY =====")

        for number, record in enumerate(records, start=1):
            print(f"\n--- Event {number} ---")
            print("Candidate:", record.get("candidate_name", "Unknown"))
            print("Candidate ID:", record.get("candidate_id", "Unknown"))
            print("Action:", record.get("action", "Unknown"))
            print("Actor:", record.get("actor", "Unknown"))
            print("Timestamp:", record.get("timestamp", "Unknown"))

        print("\nEvents displayed:", len(records))

    except PyMongoError as error:
        print("Could not retrieve audit history:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()


from pathlib import Path
from datetime import datetime, timezone
import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


BACKEND_FOLDER = Path(__file__).resolve().parent
INPUT_FILE = BACKEND_FOLDER / "candidate_batch_results.json"

load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017/"
)

DATABASE_NAME = "recruitment_system"
COLLECTION_NAME = "candidates"


def main():
    if not INPUT_FILE.exists():
        print("ERROR: candidate_batch_results.json not found.")
        print("Run batch_resume_processor.py first.")
        return

    # Read the existing candidate records.
    batch_data = json.loads(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    candidates = batch_data.get("candidates", [])

    if not candidates:
        print("No candidate records found to save.")
        return

    client = None

    try:
        # Connect to MongoDB.
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        database = client[DATABASE_NAME]
        collection = database[COLLECTION_NAME]

        inserted = 0
        updated = 0
        skipped = 0

        for candidate in candidates:
            filename = candidate.get("source_file")

            if not filename:
                print("Skipped candidate without source filename.")
                skipped += 1
                continue

            # Avoid creating duplicates when rerunning this script.
            existing = collection.find_one(
                {"source_file": filename},
                {"_id": 1}
            )

            now = datetime.now(timezone.utc)

            collection.update_one(
                {"source_file": filename},
                {
                    "$set": {
                        **candidate,
                        "updated_at": now
                    },
                    "$setOnInsert": {
                        "created_at": now
                    }
                },
                upsert=True
            )

            if existing:
                updated += 1
            else:
                inserted += 1

            print("Saved candidate:", candidate.get("name") or filename)

        print("\n===== DATABASE SAVE SUMMARY =====")
        print("New records:", inserted)
        print("Updated records:", updated)
        print("Skipped records:", skipped)
        print("Total candidates in collection:", collection.count_documents({}))

    except (PyMongoError, OSError, json.JSONDecodeError) as error:
        print("Could not save candidate records.")
        print("Error:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

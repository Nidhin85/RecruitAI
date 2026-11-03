from pathlib import Path
import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import batch_resume_processor
import database_candidate_matcher

BACKEND_FOLDER = Path(__file__).resolve().parent
load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
DATABASE_NAME = "recruitment_system"


def main():
    # Stage 1: read every PDF in sample_resumes and save candidate_batch_results.json
    batch_resume_processor.process_all_resumes()

    results_file = batch_resume_processor.OUTPUT_FILE
    if not results_file.exists():
        print("No batch results file was created.")
        return

    data = json.loads(results_file.read_text(encoding="utf-8"))
    candidates = data.get("candidates", [])

    if not candidates:
        print("No candidates were extracted from the PDFs.")
        return

    # Stage 2: add only NEW candidates to MongoDB (existing ones are not touched)
    client = None
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        collection = client[DATABASE_NAME]["candidates"]

        existing = list(collection.find({}, {"email": 1, "source_file": 1}))
        known_emails = {
            (doc.get("email") or "").strip().lower()
            for doc in existing if doc.get("email")
        }
        known_files = {
            doc.get("source_file") for doc in existing if doc.get("source_file")
        }

        added = 0
        print("\n===== ADDING TO DATABASE =====")
        for candidate in candidates:
            email = (candidate.get("email") or "").strip().lower()
            source = candidate.get("source_file")

            if (email and email in known_emails) or (source in known_files):
                print("Already in database, skipped:", source)
                continue

            collection.insert_one(dict(candidate))
            added += 1
            known_files.add(source)
            if email:
                known_emails.add(email)

            print("Added:", candidate.get("name") or "Unknown",
                  "|", email or "NO EMAIL", "|", source)

        print(f"\n{added} new candidate(s) added.")

    except PyMongoError as error:
        print("MongoDB failed:", error)
        return
    finally:
        if client is not None:
            client.close()

    # Stage 3: match every candidate against every job
    database_candidate_matcher.main()


if __name__ == "__main__":
    main()
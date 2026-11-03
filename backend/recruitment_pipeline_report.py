
from pathlib import Path
from collections import Counter
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

        collection = client[DATABASE_NAME]["candidate_matches"]
        records = list(collection.find({}))

        if not records:
            print("No candidate-job records found.")
            return

        status_counts = Counter(
            record.get("recruitment_status", "Not Set")
            for record in records
        )

        print("===== RECRUITMENT PIPELINE REPORT =====")
        print("Candidate-job records:", len(records))
        print("\nRecords by recruitment status:")

        for status, count in sorted(status_counts.items()):
            print(f"{status}: {count}")

        print("\n===== CANDIDATE DETAILS =====")

        for record in sorted(
            records,
            key=lambda item: (
                item.get("candidate_name") or ""
            ).casefold()
        ):
            print(
                f"{record.get('candidate_name', 'Unknown')} | "
                f"{record.get('job_title', 'Unknown')} | "
                f"{record.get('recruitment_status', 'Not Set')} | "
                f"Match: "
                f"{record.get('skill_match_score_percent', 0)}%"
            )

        print("\nReport generated successfully.")

    except PyMongoError as error:
        print("Could not generate report:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

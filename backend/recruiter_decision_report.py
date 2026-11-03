
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

        decisions = Counter(
            record.get("recruiter_decision", "Not Decided")
            for record in records
        )

        print("===== RECRUITER DECISION SUMMARY =====")
        print("Total candidate-job records:", len(records))

        for decision, count in sorted(decisions.items()):
            print(f"{decision}: {count}")

        print("\n===== INDIVIDUAL DECISIONS =====")

        for record in sorted(
            records,
            key=lambda item: (
                item.get("candidate_name") or ""
            ).casefold()
        ):
            print(
                f"Candidate: {record.get('candidate_name', 'Unknown')} | "
                f"Job: {record.get('job_title', 'Unknown')} | "
                f"Decision: {record.get('recruiter_decision', 'Not Decided')} "
                f"| Status: {record.get('recruitment_status', 'Not Set')}"
            )

        print("\nDecision report generated successfully.")

    except PyMongoError as error:
        print("Could not generate decision report:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

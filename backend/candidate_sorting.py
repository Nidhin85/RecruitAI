
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

SORT_OPTIONS = {
    "1": ("Highest match score", "skill_match_score_percent", -1),
    "2": ("Candidate name A-Z", "candidate_name", 1),
    "3": ("Most recently updated status", "status_updated_at", -1)
}


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME]["candidate_matches"]

        if collection.count_documents({}) == 0:
            print("No candidate records found.")
            return

        print("===== SORT CANDIDATE RECORDS =====")
        for key, (label, _, _) in SORT_OPTIONS.items():
            print(f"{key}. {label}")

        choice = input("Choose sorting option (1-3): ").strip()

        if choice not in SORT_OPTIONS:
            print("Invalid option.")
            return

        label, field, direction = SORT_OPTIONS[choice]

        records = list(
            collection.find({}).sort(field, direction)
        )

        print(f"\n===== SORTED BY {label.upper()} =====")

        for number, record in enumerate(records, start=1):
            print(f"\n{number}. {record.get('candidate_name', 'Unknown')}")
            print("Email:", record.get("candidate_email", "Not available"))
            print("Job:", record.get("job_title", "Unknown"))
            print(
                "Match score:",
                f"{record.get('skill_match_score_percent', 0)}%"
            )
            print(
                "Recruitment status:",
                record.get("recruitment_status", "Not Set")
            )

        print("\nTotal records:", len(records))

    except PyMongoError as error:
        print("Sorting failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()


from pathlib import Path
from datetime import datetime, timezone
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

STATUS_OPTIONS = {
    "1": "Application Received",
    "2": "Under Review",
    "3": "Shortlisted",
    "4": "Interview Scheduled",
    "5": "Selected",
    "6": "Rejected",
    "7": "Training Offered"
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
        results = list(
            collection.find({}).sort("candidate_name", 1)
        )

        if not results:
            print("No candidate records found.")
            return

        print("===== CANDIDATE STATUS MANAGEMENT =====")

        for number, record in enumerate(results, start=1):
            print(
                f"{number}. {record.get('candidate_name', 'Unknown')} "
                f"| {record.get('job_title', 'Unknown')} "
                f"| Status: {record.get('recruitment_status', 'Not Set')}"
            )

        try:
            selected_number = int(
                input("\nSelect a candidate number: ")
            )
        except ValueError:
            print("Enter a valid number.")
            return

        if not 1 <= selected_number <= len(results):
            print("Invalid candidate number.")
            return

        candidate = results[selected_number - 1]

        print("\nSelected candidate:", candidate.get("candidate_name"))
        print("\nChoose the new recruitment status:")

        for key, status in STATUS_OPTIONS.items():
            print(f"{key}. {status}")

        choice = input("Enter status number (1-7): ").strip()

        if choice not in STATUS_OPTIONS:
            print("Invalid status. No changes saved.")
            return

        new_status = STATUS_OPTIONS[choice]

        collection.update_one(
            {"_id": candidate["_id"]},
            {
                "$set": {
                    "recruitment_status": new_status,
                    "status_updated_at": datetime.now(timezone.utc)
                }
            }
        )

        updated = collection.find_one({"_id": candidate["_id"]})

        print("\n===== STATUS UPDATE RESULT =====")
        print("Candidate:", updated.get("candidate_name"))
        print("New status:", updated.get("recruitment_status"))
        print("Status saved in MongoDB successfully.")
        print("No email has been sent to the candidate.")

    except PyMongoError as error:
        print("Database error:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

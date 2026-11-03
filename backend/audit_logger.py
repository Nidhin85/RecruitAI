
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


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        database = client[DATABASE_NAME]
        candidates = list(
            database["candidates"].find(
                {},
                {"name": 1, "email": 1}
            )
        )

        if not candidates:
            print("No candidates found.")
            return

        print("===== AUDIT LOG TEST =====")

        for number, candidate in enumerate(candidates, start=1):
            print(
                f"{number}. {candidate.get('name', 'Unknown')} "
                f"| {candidate.get('email', 'Unknown')}"
            )

        try:
            selected_number = int(
                input("\nChoose a candidate number: ")
            )
        except ValueError:
            print("Enter a valid number.")
            return

        if not 1 <= selected_number <= len(candidates):
            print("Invalid candidate number.")
            return

        candidate = candidates[selected_number - 1]

        print("\nChoose an action to record:")
        print("1. Candidate profile reviewed")
        print("2. Candidate profile verified")
        print("3. Recruitment status reviewed")

        action_options = {
            "1": "candidate_profile_reviewed",
            "2": "candidate_profile_verified",
            "3": "recruitment_status_reviewed"
        }

        choice = input("Enter 1, 2, or 3: ").strip()

        if choice not in action_options:
            print("Invalid action. Nothing recorded.")
            return

        log_record = {
            "candidate_id": str(candidate["_id"]),
            "candidate_name": candidate.get("name", "Unknown"),
            "action": action_options[choice],
            "actor": "local_prototype_user",
            "timestamp": datetime.now(timezone.utc)
        }

        database["audit_logs"].insert_one(log_record)

        print("\nAudit event saved successfully.")
        print("Candidate:", log_record["candidate_name"])
        print("Action:", log_record["action"])
        print("Timestamp:", log_record["timestamp"])
        print("Collection: audit_logs")

    except PyMongoError as error:
        print("Audit logging failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

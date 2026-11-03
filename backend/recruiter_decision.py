
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
        matches = database["candidate_matches"]

        results = list(
            matches.find({}).sort(
                "skill_match_score_percent", -1
            )
        )

        if not results:
            print("No candidate matches found.")
            return

        print("===== RECRUITER CANDIDATE REVIEW =====")

        for index, result in enumerate(results, start=1):
            print(
                f"{index}. {result.get('candidate_name', 'Unknown')} "
                f"| Job: {result.get('job_title', 'Unknown')} "
                f"| Match: "
                f"{result.get('skill_match_score_percent', 0)}%"
            )

        try:
            selected_number = int(
                input("\nEnter the candidate number to review: ")
            )
        except ValueError:
            print("Please enter a valid number.")
            return

        if not 1 <= selected_number <= len(results):
            print("Invalid candidate number.")
            return

        candidate = results[selected_number - 1]

        print("\nCandidate:", candidate.get("candidate_name"))
        print("Email:", candidate.get("candidate_email"))
        print("Matched skills:", candidate.get("matched_skills", []))
        print("Missing skills:", candidate.get("missing_skills", []))
        print(
            "Skill match score:",
            f"{candidate.get('skill_match_score_percent', 0)}%"
        )

        print("\n1. Shortlisted")
        print("2. Rejected")
        print("3. Needs Review")

        decision_options = {
            "1": "Shortlisted",
            "2": "Rejected",
            "3": "Needs Review"
        }

        choice = input("Enter your decision (1/2/3): ").strip()

        if choice not in decision_options:
            print("Invalid decision. No changes saved.")
            return

        decision = decision_options[choice]

        result = matches.update_one(
            {"_id": candidate["_id"]},
            {
                "$set": {
                    "recruiter_decision": decision,
                    "decision_updated_at": datetime.now(timezone.utc)
                }
            }
        )

        if result.modified_count == 1:
            print("\nRecruiter decision saved:", decision)
        else:
            print(
                "\nDecision was already set to this value, "
                "or no change was needed."
            )

        print("The decision is recorded for recruiter review.")
        print("It does not automatically contact or reject the candidate.")

    except PyMongoError as error:
        print("Database error:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

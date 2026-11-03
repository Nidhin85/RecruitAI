
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

        collection = client[DATABASE_NAME]["candidate_matches"]

        results = list(
            collection.find(
                {"recruiter_decision": {"$exists": True}}
            ).sort("decision_updated_at", -1)
        )

        if not results:
            print("No saved recruiter decisions found.")
            return

        print("===== SAVED RECRUITER DECISIONS =====")

        for number, record in enumerate(results, start=1):
            print(f"\n--- Decision {number} ---")
            print("Candidate:", record.get("candidate_name", "Unknown"))
            print("Email:", record.get("candidate_email", "Not available"))
            print("Job:", record.get("job_title", "Unknown"))
            print(
                "Skill match:",
                f"{record.get('skill_match_score_percent', 0)}%"
            )
            print("Recruiter decision:", record.get("recruiter_decision"))
            print(
                "Decision updated at:",
                record.get("decision_updated_at", "Not available")
            )

        print("\nTotal saved decisions:", len(results))

    except PyMongoError as error:
        print("Could not retrieve decisions:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

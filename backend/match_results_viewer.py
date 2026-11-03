
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
COLLECTION_NAME = "candidate_matches"


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME][COLLECTION_NAME]
        results = list(
            collection.find({}).sort(
                "skill_match_score_percent", -1
            )
        )

        if not results:
            print("No matching results found.")
            return

        print("===== CANDIDATE MATCH RESULTS =====")

        for number, result in enumerate(results, start=1):
            print(f"\n--- Match {number} ---")
            print("Candidate:", result.get("candidate_name", "Unknown"))
            print("Email:", result.get("candidate_email", "Not available"))
            print("Job:", result.get("job_title", "Unknown"))
            print(
                "Skill match score:",
                f"{result.get('skill_match_score_percent', 0)}%"
            )
            print("Matched skills:", result.get("matched_skills", []))
            print("Missing skills:", result.get("missing_skills", []))
            print(
                "Recruiter review required:",
                result.get("recruiter_review_required", True)
            )

        print("\nTotal match records:", len(results))

    except PyMongoError as error:
        print("Could not retrieve match results:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

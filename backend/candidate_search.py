
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

        search_term = input(
            "Enter candidate name or email (leave blank for all): "
        ).strip()

        status_filter = input(
            "Enter recruitment status to filter "
            "(leave blank for all): "
        ).strip()

        query = {}

        if search_term:
            query["$or"] = [
                {"candidate_name": {
                    "$regex": search_term,
                    "$options": "i"
                }},
                {"candidate_email": {
                    "$regex": search_term,
                    "$options": "i"
                }}
            ]

        if status_filter:
            query["recruitment_status"] = {
                "$regex": f"^{status_filter}$",
                "$options": "i"
            }

        results = list(
            collection.find(query).sort("candidate_name", 1)
        )

        print("\n===== CANDIDATE SEARCH RESULTS =====")

        if not results:
            print("No matching candidate records found.")
            return

        for number, record in enumerate(results, start=1):
            print(f"\n--- Result {number} ---")
            print("Name:", record.get("candidate_name", "Unknown"))
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
            print(
                "Recruiter decision:",
                record.get("recruiter_decision", "Not Decided")
            )

        print("\nRecords found:", len(results))

    except PyMongoError as error:
        print("Candidate search failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

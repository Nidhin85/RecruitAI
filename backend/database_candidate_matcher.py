
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


def calculate_skill_match(candidate, required_skills):
    candidate_skills = {
        skill.strip().casefold()
        for skill in candidate.get("skills", [])
    }

    matched = [
        skill for skill in required_skills
        if skill.strip().casefold() in candidate_skills
    ]

    missing = [
        skill for skill in required_skills
        if skill.strip().casefold() not in candidate_skills
    ]

    score = round(
        len(matched) / len(required_skills) * 100,
        2
    ) if required_skills else 0

    return matched, missing, score


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        database = client[DATABASE_NAME]

        candidates_collection = database["candidates"]
        jobs_collection = database["jobs"]
        matches_collection = database["candidate_matches"]

        candidates = list(candidates_collection.find({}))
        jobs = list(jobs_collection.find({}))

        if not candidates:
            print("No candidates found in MongoDB.")
            return

        if not jobs:
            print("No job openings found in MongoDB.")
            return

        total_saved = 0

        for job in jobs:
            required_skills = job.get("required_skills", [])

            if not required_skills:
                print("Skipping job without required skills:",
                      job.get("job_title"))
                continue

            for candidate in candidates:
                matched, missing, score = calculate_skill_match(
                    candidate,
                    required_skills
                )

                # Use candidate ID and job ID to identify each match.
                candidate_id = str(candidate["_id"])
                job_id = job.get("job_id", str(job["_id"]))

                match_record = {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate.get("name"),
                    "candidate_email": candidate.get("email"),
                    "source_file": candidate.get("source_file"),
                    "job_id": job_id,
                    "job_title": job.get("job_title"),
                    "matched_skills": matched,
                    "missing_skills": missing,
                    "skill_match_score_percent": score,
                    "recruiter_review_required": True,
                    "updated_at": datetime.now(timezone.utc)
                }

                # Update the existing match instead of duplicating it.
                matches_collection.update_one(
                    {
                        "candidate_id": candidate_id,
                        "job_id": job_id
                    },
                    {
                        "$set": match_record,
                        "$setOnInsert": {
                            "created_at": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )

                total_saved += 1

                print("\nCandidate:", candidate.get("name") or "Unknown")
                print("Job:", job.get("job_title"))
                print("Skill match:", str(score) + "%")
                print("Matched:", matched)
                print("Missing:", missing)

        print("\n===== DATABASE MATCHING SUMMARY =====")
        print("Candidates read:", len(candidates))
        print("Jobs read:", len(jobs))
        print("Candidate-job matches processed:", total_saved)
        print(
            "Match records in collection:",
            matches_collection.count_documents({})
        )
        print("Results saved in MongoDB: candidate_matches")

    except PyMongoError as error:
        print("MongoDB matching failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

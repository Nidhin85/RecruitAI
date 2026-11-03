
from pathlib import Path
from datetime import datetime, timezone
import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


BACKEND_FOLDER = Path(__file__).resolve().parent
JOB_FILE = BACKEND_FOLDER / "job_description.json"

load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017/"
)

DATABASE_NAME = "recruitment_system"
COLLECTION_NAME = "jobs"


def main():
    if not JOB_FILE.exists():
        print("ERROR: job_description.json not found.")
        return

    try:
        job = json.loads(JOB_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print("Could not read the job description:", error)
        return

    title = job.get("job_title", "").strip()
    required_skills = job.get("required_skills", [])

    if not title or not required_skills:
        print("ERROR: Job title and required skills are required.")
        return

    # Give this job opening a stable ID.
    job_id = "python-developer-001"
    now = datetime.now(timezone.utc)

    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        database = client[DATABASE_NAME]
        collection = database[COLLECTION_NAME]

        # Save the job, updating it if the ID already exists.
        collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "job_title": title,
                    "description": job.get("description", ""),
                    "required_skills": required_skills,
                    "updated_at": now
                },
                "$setOnInsert": {
                    "job_id": job_id,
                    "created_at": now
                }
            },
            upsert=True
        )

        saved_job = collection.find_one(
            {"job_id": job_id},
            {"_id": 0}
        )

        print("===== JOB SAVED IN MONGODB =====")
        print("Job ID:", saved_job["job_id"])
        print("Job title:", saved_job["job_title"])
        print("Required skills:", saved_job["required_skills"])
        print("Description:", saved_job["description"])

    except PyMongoError as error:
        print("Could not save the job:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

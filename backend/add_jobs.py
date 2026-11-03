from pathlib import Path
import os
import re

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import database_candidate_matcher

BACKEND_FOLDER = Path(__file__).resolve().parent
load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
DATABASE_NAME = "recruitment_system"

# Edit this list to add your own positions. Use skill names exactly
# as they appear in candidate resumes (for example "Node.js", "MySQL").
NEW_JOBS = [
    {
        "job_title": "Python Developer",
        "required_skills": ["Python", "Flask", "SQL", "MongoDB"],
    },
    {
        "job_title": "Frontend Developer",
        "required_skills": ["HTML", "CSS", "JavaScript", "React", "Git"],
    },
    {
        "job_title": "Backend Developer",
        "required_skills": ["Python", "Django", "SQL", "MongoDB", "Git"],
    },
    {
        "job_title": "Full Stack Developer",
        "required_skills": ["JavaScript", "React", "Node.js", "MongoDB", "HTML", "CSS"],
    },
    {
        "job_title": "Database Developer",
        "required_skills": ["SQL", "MySQL", "MongoDB", "Python"],
    },
    {
        "job_title": "Software Engineer",
        "required_skills": ["C", "Python", "SQL", "JavaScript", "Git"],
    },
]


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def main():
    client = None
    added = 0

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        jobs = client[DATABASE_NAME]["jobs"]

        for job in NEW_JOBS:
            # $setOnInsert: a job that already exists is never overwritten.
            result = jobs.update_one(
                {"job_title": job["job_title"]},
                {"$setOnInsert": {
                    "job_id": f"job-{slugify(job['job_title'])}",
                    "required_skills": job["required_skills"],
                }},
                upsert=True,
            )

            if result.upserted_id:
                added += 1
                print("Added job:", job["job_title"], "->", job["required_skills"])
            else:
                print("Already exists, left unchanged:", job["job_title"])

    except PyMongoError as error:
        print("MongoDB failed:", error)
        return
    finally:
        if client is not None:
            client.close()

    print(f"\n{added} new job(s) added.\n")

    # Match every candidate against every job, including the new ones.
    database_candidate_matcher.main()


if __name__ == "__main__":
    main()
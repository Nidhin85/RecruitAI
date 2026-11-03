from pathlib import Path
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parent / ".env")

client = MongoClient(
    os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/"),
    serverSelectionTimeoutMS=3000,
)
records = list(client["recruitment_system"]["candidate_matches"].find({}))

print(f"{len(records)} candidate record(s) in the database:\n")
for r in records:
    print(
        f"- {r.get('candidate_name')} | {r.get('candidate_email')} | "
        f"{r.get('job_title')} | {r.get('skill_match_score_percent')}%"
    )

client.close()

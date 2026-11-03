from pathlib import Path
import os

from dotenv import load_dotenv
from pymongo import MongoClient

from resume_parser import extract_text
from candidate_extractor import extract_candidate_details
from candidate_validator import validate_candidate
import database_candidate_matcher

BACKEND_FOLDER = Path(__file__).resolve().parent
RESUME_FOLDER = BACKEND_FOLDER.parent / "sample_resumes"
load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
DATABASE_NAME = "recruitment_system"


def import_new_resumes():
    summary = {"pdfs_found": 0, "added": [], "skipped": [], "failed": []}

    pdf_files = sorted(RESUME_FOLDER.glob("*.pdf"))
    summary["pdfs_found"] = len(pdf_files)

    if not pdf_files:
        return summary

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        collection = client[DATABASE_NAME]["candidates"]

        existing = list(collection.find({}, {"email": 1, "source_file": 1}))
        known_emails = {
            (doc.get("email") or "").strip().lower()
            for doc in existing if doc.get("email")
        }
        known_files = {
            doc.get("source_file") for doc in existing if doc.get("source_file")
        }

        for pdf in pdf_files:
            if pdf.name in known_files:
                continue  # already imported earlier

            try:
                text = extract_text(pdf)
                if not text.strip():
                    raise ValueError("No text could be read. The PDF may be a scan.")

                candidate = extract_candidate_details(text)
                candidate = validate_candidate(candidate)
                candidate["source_file"] = pdf.name

                email = (candidate.get("email") or "").strip().lower()
                if email and email in known_emails:
                    summary["skipped"].append({
                        "file": pdf.name,
                        "reason": "Email already exists in the database",
                    })
                    continue

                collection.insert_one(dict(candidate))
                known_files.add(pdf.name)
                if email:
                    known_emails.add(email)

                summary["added"].append({
                    "file": pdf.name,
                    "name": candidate.get("name") or "Unknown",
                    "email": email,
                })
            except Exception as error:
                summary["failed"].append({"file": pdf.name, "reason": str(error)})
    finally:
        client.close()

    # Match everyone against every job, but only when something new arrived.
    if summary["added"]:
        database_candidate_matcher.main()

    return summary
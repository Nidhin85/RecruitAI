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


def main():
    pdf_files = sorted(RESUME_FOLDER.glob("*.pdf"))
    if not pdf_files:
        print("No PDF resumes found in:", RESUME_FOLDER)
        return

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    updated = 0

    try:
        client.admin.command("ping")
        collection = client[DATABASE_NAME]["candidates"]

        for pdf in pdf_files:
            try:
                text = extract_text(pdf)
                if not text.strip():
                    print("No text, skipped:", pdf.name)
                    continue

                candidate = validate_candidate(extract_candidate_details(text))
                skills = candidate.get("skills", [])
                email = (candidate.get("email") or "").strip()

                result = collection.update_one(
                    {"source_file": pdf.name}, {"$set": {"skills": skills}}
                )
                if result.matched_count == 0 and email:
                    result = collection.update_one(
                        {"email": email}, {"$set": {"skills": skills}}
                    )

                if result.matched_count:
                    updated += 1
                    print("Updated skills:", pdf.name, "->", skills)
                else:
                    print("No matching candidate in database for:", pdf.name)
            except Exception as error:
                print("Could not refresh", pdf.name, ":", error)
    finally:
        client.close()

    print(f"\n{updated} candidate(s) refreshed.\n")

    if updated:
        database_candidate_matcher.main()


if __name__ == "__main__":
    main()
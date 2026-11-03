
from pathlib import Path
from datetime import datetime, timezone
import csv
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

OUTPUT_FILE = BACKEND_FOLDER / "recruitment_pipeline_export.csv"


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME]["candidate_matches"]
        records = list(
            collection.find({}).sort("candidate_name", 1)
        )

        if not records:
            print("No candidate-job records available to export.")
            return

        columns = [
            "candidate_name",
            "candidate_email",
            "job_title",
            "skill_match_score_percent",
            "matched_skills",
            "missing_skills",
            "recruiter_decision",
            "recruitment_status",
            "recruiter_review_required",
            "source_file"
        ]

        with OUTPUT_FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=columns,
                extrasaction="ignore"
            )
            writer.writeheader()

            for record in records:
                row = {
                    key: record.get(key, "")
                    for key in columns
                }

                row["matched_skills"] = ", ".join(
                    record.get("matched_skills", [])
                )
                row["missing_skills"] = ", ".join(
                    record.get("missing_skills", [])
                )

                writer.writerow(row)

        print("===== CSV EXPORT SUCCESSFUL =====")
        print("Records exported:", len(records))
        print("Output file:", OUTPUT_FILE)

    except (PyMongoError, OSError, csv.Error) as error:
        print("Report export failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()


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
PAGE_SIZE = 2


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME]["candidate_matches"]

        total_records = collection.count_documents({})
        if total_records == 0:
            print("No candidate records found.")
            return

        total_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE

        print("===== CANDIDATE PAGINATION =====")
        print("Total records:", total_records)
        print("Records per page:", PAGE_SIZE)
        print("Total pages:", total_pages)

        while True:
            page_input = input(
                f"\nEnter page number (1-{total_pages}), "
                "or Q to quit: "
            ).strip()

            if page_input.casefold() == "q":
                print("Pagination finished.")
                break

            try:
                page_number = int(page_input)
            except ValueError:
                print("Enter a valid page number.")
                continue

            if not 1 <= page_number <= total_pages:
                print("Page number is out of range.")
                continue

            skip_count = (page_number - 1) * PAGE_SIZE

            records = list(
                collection.find({})
                .sort("candidate_name", 1)
                .skip(skip_count)
                .limit(PAGE_SIZE)
            )

            print(f"\n===== PAGE {page_number} =====")

            for record in records:
                print("\nCandidate:", record.get("candidate_name", "Unknown"))
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

            print("Records on this page:", len(records))

    except PyMongoError as error:
        print("Pagination failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

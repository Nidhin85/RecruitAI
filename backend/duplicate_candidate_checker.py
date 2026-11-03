
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


def normalize(value):
    """Normalize an email or phone number for comparison."""
    return "".join(
        character for character in (value or "").casefold()
        if character.isalnum()
    )


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME]["candidates"]
        candidates = list(collection.find({}))

        if not candidates:
            print("No candidates found.")
            return

        email_groups = {}
        phone_groups = {}

        for candidate in candidates:
            email = normalize(candidate.get("email"))
            phone = normalize(candidate.get("phone"))

            if email:
                email_groups.setdefault(email, []).append(candidate)

            if phone:
                phone_groups.setdefault(phone, []).append(candidate)

        duplicate_groups = []

        for email, group in email_groups.items():
            if len(group) > 1:
                duplicate_groups.append(("Email", email, group))

        for phone, group in phone_groups.items():
            if len(group) > 1:
                duplicate_groups.append(("Phone", phone, group))

        print("===== DUPLICATE CANDIDATE CHECK =====")
        print("Candidate records checked:", len(candidates))

        if not duplicate_groups:
            print("No possible duplicates found.")
        else:
            print("Possible duplicate groups:", len(duplicate_groups))

            for match_type, value, group in duplicate_groups:
                print(f"\nMatching {match_type}: {value}")
                for candidate in group:
                    print(
                        "-",
                        candidate.get("name", "Unknown"),
                        "|",
                        candidate.get("email", "No email"),
                        "|",
                        candidate.get("phone", "No phone"),
                        "| Source:",
                        candidate.get("source_file", "Unknown")
                    )

        print(
            "\nCheck complete. No candidate records were changed."
        )

    except PyMongoError as error:
        print("Duplicate check failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()


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

        collection = client[DATABASE_NAME]["candidates"]

        email = input(
            "Enter the candidate's email address: "
        ).strip()

        if not email:
            print("Email address cannot be empty.")
            return

        candidate = collection.find_one({
            "email": {
                "$regex": f"^{email}$",
                "$options": "i"
            }
        })

        if not candidate:
            print("No candidate found with that email.")
            return

        print("\n===== CANDIDATE PROFILE =====")
        print("Name:", candidate.get("name", "Not available"))
        print("Email:", candidate.get("email", "Not available"))
        print("Phone:", candidate.get("phone", "Not available"))
        print("Skills:", candidate.get("skills", []))
        print("Education:", candidate.get("education", []))
        print("Experience:", candidate.get("experience", []))
        print("Resume file:", candidate.get("source_file", "Not available"))
        print(
            "Recruiter verification required:",
            candidate.get("verification_required", True)
        )
        print(
            "Verified by recruiter:",
            candidate.get("verified_by_recruiter", False)
        )
        print(
            "Validation issues:",
            candidate.get("validation_issues", [])
        )

        print("\nProfile retrieved successfully.")
        print("This tool does not modify candidate data.")

    except PyMongoError as error:
        print("Could not retrieve candidate profile:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

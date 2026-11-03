
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


def main():
    client = None

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")

        collection = client[DATABASE_NAME]["candidates"]

        email = input("Enter candidate email: ").strip()

        if not email:
            print("Email cannot be empty.")
            return

        candidate = collection.find_one({
            "email": {
                "$regex": f"^{email}$",
                "$options": "i"
            }
        })

        if not candidate:
            print("Candidate not found.")
            return

        print("\n===== PROFILE VERIFICATION =====")
        print("Name:", candidate.get("name", "Unknown"))
        print("Email:", candidate.get("email", "Unknown"))
        print("Phone:", candidate.get("phone", "Unknown"))
        print("Skills:", candidate.get("skills", []))
        print("Education:", candidate.get("education", []))
        print("Experience:", candidate.get("experience", []))
        print("Current verification:", candidate.get(
            "verified_by_recruiter", False
        ))

        print("\nReview the candidate details before continuing.")
        print("1. Mark profile as verified")
        print("2. Keep profile unverified")

        choice = input("Choose 1 or 2: ").strip()

        if choice not in ("1", "2"):
            print("Invalid choice. No changes saved.")
            return

        verified = choice == "1"

        update_fields = {
            "verified_by_recruiter": verified,
            "verification_required": not verified,
            "verification_updated_at": datetime.now(timezone.utc)
        }

        collection.update_one(
            {"_id": candidate["_id"]},
            {"$set": update_fields}
        )

        print("\nVerification status saved.")
        print("Verified by recruiter:", verified)
        print("Verification required:", not verified)

    except PyMongoError as error:
        print("Verification update failed:", error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()

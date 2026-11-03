
from pathlib import Path
import json
import re

BACKEND_FOLDER = Path(__file__).resolve().parent
INPUT_FILE = BACKEND_FOLDER / "candidate_data.json"
OUTPUT_FILE = BACKEND_FOLDER / "validated_candidate_data.json"


def validate_candidate(candidate):
    """Check candidate fields and identify information needing review."""

    issues = []

    # Check candidate name.
    name = candidate.get("name")

    if not name or not name.strip():
        issues.append("Candidate name is missing.")

    # Check email format.
    email = candidate.get("email")

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if not email:
        issues.append("Email address is missing.")
    elif not re.fullmatch(email_pattern, email.strip()):
        issues.append("Email format appears invalid.")

    # Check phone number format.
    phone = candidate.get("phone")

    if not phone:
        issues.append("Phone number is missing.")
    else:
        digits = re.sub(r"\D", "", phone)

        if not 7 <= len(digits) <= 15:
            issues.append("Phone number length needs verification.")

    # Check skills.
    skills = candidate.get("skills", [])

    if not skills:
        issues.append("No recognized skills were extracted.")

    # Add validation results.
    candidate["validation_issues"] = issues
    candidate["needs_recruiter_review"] = len(issues) > 0
    candidate["verified_by_recruiter"] = False

    return candidate


def main():
    if not INPUT_FILE.exists():
        print("ERROR: candidate_data.json was not found.")
        print("Run candidate_extractor.py first.")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        candidate = json.load(file)

    validated_candidate = validate_candidate(candidate)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            validated_candidate,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("===== CANDIDATE VALIDATION RESULT =====")
    print(json.dumps(validated_candidate, indent=4, ensure_ascii=False))

    if validated_candidate["needs_recruiter_review"]:
        print("\nStatus: REVIEW REQUIRED")
    else:
        print("\nStatus: BASIC FORMAT CHECKS PASSED")

    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

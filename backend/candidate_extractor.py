
from pathlib import Path
import re
import json


# Find the backend folder.
BACKEND_FOLDER = Path(__file__).resolve().parent

# Read the text extracted from the PDF.
TEXT_FILE = BACKEND_FOLDER / "extracted_resume.txt"

# Save the extracted candidate details here.
OUTPUT_FILE = BACKEND_FOLDER / "candidate_data.json"


def extract_candidate_details(text):
    """Extract basic candidate details from resume text."""

    # Find the first non-empty line as a possible name.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else None

    # Find email address.
    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text
    )
    email = email_match.group(0) if email_match else None

    # Find phone number.
    phone_match = re.search(
        r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)",
        text
    )
    phone = phone_match.group(0).strip() if phone_match else None

    # Find skills using a predefined list.
    known_skills = [
        "Python", "Java", "JavaScript", "Flask",
        "Django", "SQL", "MySQL", "MongoDB", "React",
        "Node.js", "HTML", "CSS", "Bootstrap",
        "Machine Learning", "Git", "REST APIs",
        "PyMuPDF", "Postman", "C++", "C"
    ]

    # Single letters and symbols need exact capitalisation.
    case_sensitive_skills = {"C", "C++"}

    matched_skills = []

    for skill in known_skills:
        pattern = r"(?<![\w+#])" + re.escape(skill) + r"(?![\w+#])"
        flags = 0 if skill in case_sensitive_skills else re.IGNORECASE

        if re.search(pattern, text, flags):
            matched_skills.append(skill)

    # Find education-related lines.
    education_keywords = [
        "B.Tech", "BTech", "Bachelor", "Master",
        "Degree", "University", "College", "Education"
    ]

    education = [
        line for line in lines
        if any(word.lower() in line.lower()
               for word in education_keywords)
    ]

    # Find experience statements mentioning years.
    experience = re.findall(
        r"\b\d+(?:\.\d+)?\s*\+?\s*years?\b",
        text,
        re.IGNORECASE
    )

    # Mark fields that need manual verification.
    candidate = {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": matched_skills,
        "education": education,
        "experience_mentions": experience,
        "verification_required": True,
        "verified_by_recruiter": False
    }

    return candidate


def main():
    if not TEXT_FILE.exists():
        print("ERROR: Extracted text file not found.")
        print("Run resume_parser.py first.")
        return

    # Read the extracted resume text.
    text = TEXT_FILE.read_text(encoding="utf-8")

    # Extract candidate information.
    candidate = extract_candidate_details(text)

    # Save the results as formatted JSON.
    OUTPUT_FILE.write_text(
        json.dumps(candidate, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("===== EXTRACTED CANDIDATE DETAILS =====")
    print(json.dumps(candidate, indent=4, ensure_ascii=False))
    print("\nSaved candidate data to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

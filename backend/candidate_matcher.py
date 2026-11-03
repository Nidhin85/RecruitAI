
from pathlib import Path
import json

BACKEND_FOLDER = Path(__file__).resolve().parent

CANDIDATES_FILE = BACKEND_FOLDER / "candidate_batch_results.json"
JOB_FILE = BACKEND_FOLDER / "job_description.json"
OUTPUT_FILE = BACKEND_FOLDER / "candidate_match_results.json"


def match_candidate(candidate, required_skills):
    # Convert skills to lowercase for comparison.
    candidate_skills = {
        skill.strip().casefold()
        for skill in candidate.get("skills", [])
    }

    matched_skills = []
    missing_skills = []

    # Compare each job requirement with candidate skills.
    for skill in required_skills:
        if skill.strip().casefold() in candidate_skills:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    # Calculate the percentage of required skills matched.
    if required_skills:
        score = round(
            len(matched_skills) / len(required_skills) * 100,
            2
        )
    else:
        score = 0

    return {
        "name": candidate.get("name"),
        "email": candidate.get("email"),
        "source_file": candidate.get("source_file"),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_skill_count": len(matched_skills),
        "required_skill_count": len(required_skills),
        "skill_match_score_percent": score,
        "needs_recruiter_review": True
    }


def main():
    # Check whether the required files exist.
    if not CANDIDATES_FILE.exists():
        print("ERROR: Candidate batch results not found.")
        print("Run batch_resume_processor.py first.")
        return

    if not JOB_FILE.exists():
        print("ERROR: job_description.json not found.")
        return

    # Load candidate records and job requirements.
    candidates_data = json.loads(
        CANDIDATES_FILE.read_text(encoding="utf-8")
    )

    job = json.loads(
        JOB_FILE.read_text(encoding="utf-8")
    )

    required_skills = job.get("required_skills", [])

    if not required_skills:
        print("ERROR: Add required skills to the job description.")
        return

    results = []

    # Match every successfully processed candidate.
    for candidate in candidates_data.get("candidates", []):
        result = match_candidate(candidate, required_skills)
        results.append(result)

    # Sort by skill match score, highest first.
    results.sort(
        key=lambda item: item["skill_match_score_percent"],
        reverse=True
    )

    output = {
        "job_title": job.get("job_title"),
        "matching_method": "Exact skill matching baseline",
        "score_explanation": (
            "Percentage of listed required skills found in "
            "the extracted candidate skills. Not a hiring probability."
        ),
        "candidates": results
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("===== CANDIDATE MATCHING RESULTS =====")
    print("Job:", job.get("job_title"))

    for index, candidate in enumerate(results, start=1):
        print(f"\n{index}. {candidate.get('name') or 'Unknown'}")
        print(
            "Skill match:",
            str(candidate["skill_match_score_percent"]) + "%"
        )
        print("Matched skills:", candidate["matched_skills"])
        print("Missing skills:", candidate["missing_skills"])

    print("\nSaved results to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()


from pathlib import Path
import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from resume_parser import extract_text


BACKEND_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = BACKEND_FOLDER.parent
RESUME_FOLDER = PROJECT_FOLDER / "sample_resumes"

CANDIDATES_FILE = BACKEND_FOLDER / "candidate_batch_results.json"
JOB_FILE = BACKEND_FOLDER / "job_description.json"
OUTPUT_FILE = BACKEND_FOLDER / "semantic_match_results.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    # Load previously extracted candidate details.
    candidates_data = json.loads(
        CANDIDATES_FILE.read_text(encoding="utf-8")
    )

    # Load the job description.
    job = json.loads(
        JOB_FILE.read_text(encoding="utf-8")
    )

    required_skills = job.get("required_skills", [])
    job_description = job.get("description", "")

    if not required_skills or not job_description.strip():
        print("ERROR: Job description and required skills are needed.")
        return

    # Load the AI text-embedding model.
    print("Loading semantic AI model...")
    model = SentenceTransformer(MODEL_NAME)

    # Encode the job description and each required skill.
    skill_embeddings = model.encode(required_skills)
    results = []

    for candidate in candidates_data.get("candidates", []):
        filename = candidate.get("source_file")

        if not filename:
            print("Skipping candidate without a source filename.")
            continue

        pdf_path = RESUME_FOLDER / filename

        if not pdf_path.is_file():
            print("Resume file not found:", filename)
            continue

        # Extract the original resume text.
        resume_text = extract_text(pdf_path)

        if not resume_text.strip():
            print("No readable text found in:", filename)
            continue

        # Compare the job description with the entire resume.
        description_embeddings = model.encode(
            [job_description, resume_text]
        )

        overall_similarity = cosine_similarity(
            description_embeddings[0].reshape(1, -1),
            description_embeddings[1].reshape(1, -1)
        )[0][0]

        # Compare each required skill with the resume text.
        resume_embedding = model.encode([resume_text])

        skill_scores = cosine_similarity(
            skill_embeddings,
            resume_embedding
        ).flatten()

        skill_results = []

        for skill, score in zip(required_skills, skill_scores):
            skill_results.append({
                "skill": skill,
                "similarity_percent": round(float(score) * 100, 2),
                "needs_verification": True
            })

        results.append({
            "name": candidate.get("name"),
            "email": candidate.get("email"),
            "source_file": filename,
            "job_title": job.get("job_title"),
            "overall_text_similarity_percent": round(
                float(overall_similarity) * 100, 2
            ),
            "skill_similarity": skill_results,
            "recruiter_review_required": True
        })

    output = {
        "matching_method": "Sentence Transformers cosine similarity",
        "note": (
            "Similarity scores measure textual similarity, not hiring "
            "probability or proven skill. Review resume evidence manually."
        ),
        "results": results
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== SEMANTIC MATCHING RESULTS =====")

    for candidate in results:
        print("\nCandidate:", candidate.get("name") or "Unknown")
        print(
            "Overall text similarity:",
            str(candidate["overall_text_similarity_percent"]) + "%"
        )

        for skill in candidate["skill_similarity"]:
            print(
                skill["skill"] + ":",
                str(skill["similarity_percent"]) + "%"
            )

    print("\nResults saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

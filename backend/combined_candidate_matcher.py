
from pathlib import Path
import json

BACKEND_FOLDER = Path(__file__).resolve().parent

EXACT_FILE = BACKEND_FOLDER / "candidate_match_results.json"
SEMANTIC_FILE = BACKEND_FOLDER / "semantic_match_results.json"
OUTPUT_FILE = BACKEND_FOLDER / "combined_match_results.json"


def main():
    # Load exact skill matching results.
    if not EXACT_FILE.exists() or not SEMANTIC_FILE.exists():
        print("ERROR: One or both matching result files are missing.")
        print("Run candidate_matcher.py and semantic_candidate_matcher.py first.")
        return

    exact_data = json.loads(
        EXACT_FILE.read_text(encoding="utf-8")
    )

    semantic_data = json.loads(
        SEMANTIC_FILE.read_text(encoding="utf-8")
    )

    # Index semantic results by their source PDF filename.
    semantic_by_file = {
        item.get("source_file"): item
        for item in semantic_data.get("results", [])
    }

    combined_results = []

    for exact in exact_data.get("candidates", []):
        filename = exact.get("source_file")
        semantic = semantic_by_file.get(filename)

        if semantic is None:
            print("No semantic result found for:", filename)
            continue

        exact_score = exact.get("skill_match_score_percent", 0)
        semantic_score = semantic.get(
            "overall_text_similarity_percent", 0
        )

        # Weighted ranking: 60% exact skill coverage,
        # 40% semantic text similarity.
        combined_score = round(
            (0.60 * exact_score) + (0.40 * semantic_score),
            2
        )

        combined_results.append({
            "name": exact.get("name"),
            "email": exact.get("email"),
            "source_file": filename,
            "exact_skill_match_percent": exact_score,
            "semantic_text_similarity_percent": semantic_score,
            "combined_ranking_score": combined_score,
            "matched_skills": exact.get("matched_skills", []),
            "missing_skills": exact.get("missing_skills", []),
            "recruiter_review_required": True
        })

    # Sort highest ranking score first.
    combined_results.sort(
        key=lambda item: item["combined_ranking_score"],
        reverse=True
    )

    output = {
        "method": "60% exact skill coverage + 40% semantic similarity",
        "warning": (
            "This experimental ranking is not a hiring probability. "
            "Semantic similarity is not proof of skill. Recruiters must "
            "review resume evidence and make all hiring decisions."
        ),
        "candidates": combined_results
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("===== COMBINED CANDIDATE RANKING =====")

    for position, candidate in enumerate(combined_results, start=1):
        print(f"\nRank: {position}")
        print("Name:", candidate.get("name") or "Unknown")
        print(
            "Combined ranking score:",
            str(candidate["combined_ranking_score"]) + "%"
        )
        print("Matched skills:", candidate["matched_skills"])
        print("Missing skills:", candidate["missing_skills"])

    print("\nResults saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

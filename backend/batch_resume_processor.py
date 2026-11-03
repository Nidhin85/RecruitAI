
from pathlib import Path
import json

from resume_parser import extract_text
from candidate_extractor import extract_candidate_details
from candidate_validator import validate_candidate


# Locate the project folders.
BACKEND_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = BACKEND_FOLDER.parent
RESUME_FOLDER = PROJECT_FOLDER / "sample_resumes"

# Store all results in one file.
OUTPUT_FILE = BACKEND_FOLDER / "candidate_batch_results.json"


def process_all_resumes():
    # Find all PDF resumes in the sample folder.
    pdf_files = sorted(RESUME_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print("No PDF resumes found in:", RESUME_FOLDER)
        print("Add at least one PDF resume and try again.")
        return

    results = []
    errors = []

    print(f"Found {len(pdf_files)} PDF resume(s).")

    # Process each PDF separately.
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")

        try:
            # Step 1: Extract text from the PDF.
            text = extract_text(pdf_file)

            if not text.strip():
                raise ValueError(
                    "No text extracted. The PDF may be scanned "
                    "or contain no readable text."
                )

            # Step 2: Extract candidate details.
            candidate = extract_candidate_details(text)

            # Step 3: Validate candidate fields.
            candidate = validate_candidate(candidate)

            # Track the original PDF filename.
            candidate["source_file"] = pdf_file.name

            # Store this candidate's result.
            results.append(candidate)

            print("Candidate:", candidate.get("name") or "Unknown")
            print(
                "Needs review:",
                candidate["needs_recruiter_review"]
            )

        except Exception as error:
            # Keep processing other files if one PDF fails.
            errors.append({
                "source_file": pdf_file.name,
                "error": str(error)
            })

            print("Could not process this PDF:", error)

    # Save all successful results and file errors.
    batch_data = {
        "total_pdfs_found": len(pdf_files),
        "successfully_processed": len(results),
        "failed_files": len(errors),
        "candidates": results,
        "errors": errors
    }

    OUTPUT_FILE.write_text(
        json.dumps(batch_data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== BATCH PROCESSING SUMMARY =====")
    print("PDFs found:", len(pdf_files))
    print("Successfully processed:", len(results))
    print("Failed files:", len(errors))
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    process_all_resumes()

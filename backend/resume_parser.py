
from pathlib import Path
import pymupdf  # PyMuPDF


def extract_text(pdf_path):
    """Extract text from every page of a PDF."""

    pdf_path = Path(pdf_path)

    # Check whether the PDF file exists.
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Open the PDF document.
    document = pymupdf.open(pdf_path)

    extracted_text = ""

    try:
        # Read each page one by one.
        for page in document:
            page_text = page.get_text("text")
            extracted_text += page_text + "\n"

    finally:
        # Close the PDF after reading it.
        document.close()

    return extracted_text.strip()


if __name__ == "__main__":
    # Find the sample PDF in the project folder.
    project_folder = Path(__file__).resolve().parent.parent
    pdf_file = project_folder / "sample_resumes" / "arun_resume.pdf"

    try:
        # Extract the text.
        text = extract_text(pdf_file)

        # Display the extracted text.
        print("===== EXTRACTED RESUME TEXT =====")
        print(text)

        # Save the text to a new file.
        output_file = Path(__file__).resolve().parent / "extracted_resume.txt"
        output_file.write_text(text, encoding="utf-8")

        print("\nText saved to:", output_file)

    except FileNotFoundError as error:
        print("File error:", error)

    except Exception as error:
        print("Could not read the PDF:", error)

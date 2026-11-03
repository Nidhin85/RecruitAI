import json
import re
import threading
from pathlib import Path
import os
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename
BACKEND_FOLDER = Path(__file__).resolve().parent
load_dotenv(BACKEND_FOLDER / ".env")

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017/"
)
DATABASE_NAME = "recruitment_system"


from bson import ObjectId
from flask.json.provider import DefaultJSONProvider


class MongoJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, ObjectId):
            return str(obj)

        return DefaultJSONProvider.default(obj)


app = Flask(__name__)
app.json = MongoJSONProvider(app)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB per upload
RESUME_FOLDER = BACKEND_FOLDER.parent / "sample_resumes"


def get_database():
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=3000
    )
    client.admin.command("ping")
    return client


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Recruitment Management API is running"
    })


@app.route("/api/candidates/matches", methods=["GET"])
def get_candidate_matches():
    client = None

    try:
        client = get_database()
        collection = client[DATABASE_NAME]["candidate_matches"]

        records = list(
            collection.find({}).sort(
                "skill_match_score_percent", -1
            )
        )

        results = []

        for record in records:
            results.append({
                "candidate_name": record.get(
                    "candidate_name", "Unknown"
                ),
                "candidate_email": record.get(
                    "candidate_email", ""
                ),
                "job_title": record.get("job_title", "Unknown"),
                "skill_match_score_percent": record.get(
                    "skill_match_score_percent", 0
                ),
                "matched_skills": record.get("matched_skills", []),
                "missing_skills": record.get("missing_skills", []),
                "recruiter_decision": record.get(
                    "recruiter_decision", "Not Decided"
                ),
                "recruitment_status": record.get(
                    "recruitment_status", "Not Set"
                )
            })

        return jsonify({
            "total": len(results),
            "candidates": results
        }), 200

    except PyMongoError:
        app.logger.exception("Could not retrieve candidate matches")
        return jsonify({
            "error": "Unable to retrieve candidate matches"
        }), 500

    finally:
        if client is not None:
            client.close()


# STEP 6: UPDATE CANDIDATE DECISION
@app.route("/api/candidates/decision", methods=["PUT"])
def update_candidate_decision():
    data = request.get_json(silent=True) or {}

    candidate_email = data.get("candidate_email")
    job_title = data.get("job_title")
    decision = data.get("recruiter_decision")

    allowed_decisions = {
        "Not Decided",
        "Under Review",
        "Shortlisted",
        "Rejected"
    }

    if not all(
        isinstance(value, str) and value.strip()
        for value in (candidate_email, job_title, decision)
    ):
        return jsonify({
            "success": False,
            "message": "Candidate email, job title, and decision are required."
        }), 400

    candidate_email = candidate_email.strip()
    job_title = job_title.strip()
    decision = decision.strip()

    if decision not in allowed_decisions:
        return jsonify({
            "success": False,
            "message": "Invalid decision."
        }), 400

    client = None

    try:
        client = get_database()
        collection = client[DATABASE_NAME]["candidate_matches"]

        result = collection.update_one(
            {
                "candidate_email": candidate_email,
                "job_title": job_title
            },
            {
                "$set": {
                    "recruiter_decision": decision
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({
                "success": False,
                "message": "Candidate record not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Candidate decision saved.",
            "recruiter_decision": decision
        }), 200

    except PyMongoError:
        app.logger.exception("Could not update candidate decision")
        return jsonify({
            "success": False,
            "message": "Unable to save candidate decision."
        }), 500

    finally:
        if client is not None:
            client.close()


# DAY 6 - STEP 7: PERMANENT INTERVIEW STORAGE

@app.route("/api/interviews", methods=["GET"])
def get_interviews():
    client = None

    try:
        client = get_database()
        collection = client[DATABASE_NAME]["interviews"]

        records = list(
            collection.find({}).sort("_id", -1)
        )

        interviews = []

        for record in records:
            interviews.append({
                "id": str(record["_id"]),
                "status": record.get("status", "Scheduled"),
                "candidate_name": record.get("candidate_name", ""),
                "candidate_email": record.get("candidate_email", ""),
                "job_title": record.get("job_title", ""),
                "date": record.get("date", ""),
                "time": record.get("time", ""),
                "duration": record.get("duration", 30),
                "mode": record.get("mode", "Online"),
                "notes": record.get("notes", "")
            })

        return jsonify({
            "success": True,
            "interviews": interviews
        }), 200

    except PyMongoError:
        app.logger.exception("Could not retrieve interviews")
        return jsonify({
            "success": False,
            "message": "Unable to retrieve interviews."
        }), 500

    finally:
        if client is not None:
            client.close()



@app.route("/api/interviews", methods=["POST"])
def create_interview():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "candidate_name",
        "candidate_email",
        "job_title",
        "date",
        "time"
    ]

    for field in required_fields:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return jsonify({
                "success": False,
                "message": f"{field.replace('_', ' ').title()} is required."
            }), 400

    try:
        duration = int(data.get("duration", 30))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Duration must be a number."
        }), 400

    if duration not in (15, 30, 45, 60):
        return jsonify({
            "success": False,
            "message": "Duration must be 15, 30, 45, or 60 minutes."
        }), 400

    mode = data.get("mode", "Online")
    if mode not in ("Online", "In Person"):
        return jsonify({
            "success": False,
            "message": "Mode must be Online or In Person."
        }), 400

    interview = {
        "candidate_name": data["candidate_name"].strip(),
        "candidate_email": data["candidate_email"].strip().lower(),
        "job_title": data["job_title"].strip(),
        "date": data["date"].strip(),
        "time": data["time"].strip(),
        "duration": duration,
        "mode": mode,
        "notes": str(data.get("notes", "")).strip()
    }

    client = None

    try:
        client = get_database()
        collection = client[DATABASE_NAME]["interviews"]

        duplicate = collection.find_one({
            "candidate_email": {
                "$regex": f"^{re.escape(interview['candidate_email'])}$",
                "$options": "i"
            },
            "date": interview["date"],
            "time": interview["time"],
            "status": {"$ne": "Cancelled"}
        })

        if duplicate:
            return jsonify({
                "success": False,
                "message": (
                    "This candidate already has an interview "
                    "scheduled for this date and time."
                )
            }), 409

        result = collection.insert_one(interview)

        return jsonify({
            "success": True,
            "message": "Interview saved successfully.",
            "interview": {
                "id": str(result.inserted_id),
                "status": "Scheduled",
                **interview
            }
        }), 201

    except PyMongoError:
        app.logger.exception("Could not save interview")
        return jsonify({
            "success": False,
            "message": "Unable to save interview."
        }), 500

    finally:
        if client is not None:
            client.close()


@app.route("/api/interviews/status", methods=["PUT"])
def update_interview_status():
    data = request.get_json(silent=True) or {}

    interview_id = data.get("id")
    status = data.get("status")

    allowed_statuses = {
        "Scheduled",
        "Completed",
        "Cancelled"
    }

    if not isinstance(interview_id, str) or not interview_id.strip():
        return jsonify({
            "success": False,
            "message": "Interview ID is required."
        }), 400

    if status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid interview status."
        }), 400

    try:
        object_id = ObjectId(interview_id)
    except Exception:
        return jsonify({
            "success": False,
            "message": "Invalid interview ID."
        }), 400

    client = None

    try:
        client = get_database()
        collection = client[DATABASE_NAME]["interviews"]

        result = collection.update_one(
            {"_id": object_id},
            {"$set": {"status": status}}
        )

        if result.matched_count == 0:
            return jsonify({
                "success": False,
                "message": "Interview not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Interview status updated.",
            "status": status
        }), 200

    except PyMongoError:
        app.logger.exception("Could not update interview status")
        return jsonify({
            "success": False,
            "message": "Unable to update interview status."
        }), 500

    finally:
        if client is not None:
            client.close()


@app.route("/api/interviews/<interview_id>", methods=["PUT"])
def edit_interview(interview_id):
    data = request.get_json(silent=True) or {}

    try:
        object_id = ObjectId(interview_id)
    except Exception:
        return jsonify({
            "success": False,
            "message": "Invalid interview ID."
        }), 400

    required_fields = ["date", "time", "duration", "mode"]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"{field.title()} is required."
            }), 400

    try:
        duration = int(data["duration"])
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Duration must be a number."
        }), 400

    if duration not in (15, 30, 45, 60):
        return jsonify({
            "success": False,
            "message": "Duration must be 15, 30, 45, or 60 minutes."
        }), 400

    if data["mode"] not in ("Online", "In Person"):
        return jsonify({
            "success": False,
            "message": "Mode must be Online or In Person."
        }), 400

    if not isinstance(data["date"], str) or not data["date"].strip():
        return jsonify({
            "success": False,
            "message": "A valid date is required."
        }), 400

    if not isinstance(data["time"], str) or not data["time"].strip():
        return jsonify({
            "success": False,
            "message": "A valid time is required."
        }), 400

    client = None

    try:
        client = get_database()
        collection = client[DATABASE_NAME]["interviews"]

        existing = collection.find_one({"_id": object_id})

        if not existing:
            return jsonify({
                "success": False,
                "message": "Interview not found."
            }), 404

        if existing.get("status", "Scheduled") == "Cancelled":
            return jsonify({
                "success": False,
                "message": "Cancelled interviews cannot be edited."
            }), 400

        duplicate = collection.find_one({
            "_id": {"$ne": object_id},
            "candidate_email": existing.get("candidate_email", ""),
            "date": data["date"].strip(),
            "time": data["time"].strip(),
            "status": {"$ne": "Cancelled"}
        })

        if duplicate:
            return jsonify({
                "success": False,
                "message": "Another interview exists at this date and time."
            }), 409

        collection.update_one(
            {"_id": object_id},
            {"$set": {
                "date": data["date"].strip(),
                "time": data["time"].strip(),
                "duration": duration,
                "mode": data["mode"],
                "notes": str(data.get("notes", "")).strip()
            }}
        )

        return jsonify({
            "success": True,
            "message": "Interview updated successfully."
        }), 200

    except PyMongoError:
        app.logger.exception("Could not edit interview")
        return jsonify({
            "success": False,
            "message": "Unable to update interview."
        }), 500

    finally:
        if client is not None:
            client.close()


# RecruitAI email test log: records an editable invitation without sending it.
@app.route("/api/email/test-log", methods=["POST"])
def save_email_test_log():
    data = request.get_json(silent=True) or {}
    required_fields = ["candidate_name", "candidate_email", "job_title", "subject", "body"]

    for field in required_fields:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return jsonify({
                "success": False,
                "message": f"{field.replace('_', ' ').title()} is required."
            }), 400

    # This endpoint is intentionally test-only and never sends email.
    email_record = {
        "candidate_name": data["candidate_name"].strip(),
        "candidate_email": data["candidate_email"].strip(),
        "job_title": data["job_title"].strip(),
        "subject": data["subject"].strip(),
        "body": data["body"],
        "interview_date": str(data.get("interview_date", "")).strip(),
        "interview_time": str(data.get("interview_time", "")).strip(),
        "duration": data.get("duration", 30),
        "mode": str(data.get("mode", "Online")).strip(),
        "status": "Test Sent (Not Delivered)",
        "test_mode": True,
    }

    client = None
    try:
        client = get_database()
        result = client[DATABASE_NAME]["email_test_logs"].insert_one(email_record)
        return jsonify({
            "success": True,
            "message": "Test email saved successfully. No real email was sent.",
            "email_id": str(result.inserted_id),
            "status": email_record["status"],
        }), 201
    except PyMongoError:
        app.logger.exception("Could not save RecruitAI email test log")
        return jsonify({
            "success": False,
            "message": "Unable to save the test email. Check that MongoDB is running."
        }), 500
    finally:
        if client is not None:
            client.close()

def build_candidate_insights(job_title, score, matched, missing):
    matched = [str(s).strip() for s in (matched or []) if str(s).strip()]
    missing = [str(s).strip() for s in (missing or []) if str(s).strip()]

    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0

    if score >= 80:
        level = "a strong"
    elif score >= 60:
        level = "a good"
    elif score >= 40:
        level = "a partial"
    else:
        level = "a limited"

    summary = f"This candidate is {level} skill match for the {job_title} role at {score:g}%."
    if matched:
        summary += f" They cover {len(matched)} required skill(s), including {', '.join(matched[:3])}."
    if missing:
        summary += f" {len(missing)} required skill(s) are missing: {', '.join(missing[:3])}."
    else:
        summary += " No required skills are missing."

    strengths = [f"Matches the required skill: {skill}" for skill in matched[:3]]
    if score >= 80:
        strengths.append("High overall skill coverage for this role.")
    if not strengths:
        strengths = ["No matched skills were reported."]

    gaps = [
        f"No evidence of {skill}. Ask how they would learn or cover it."
        for skill in missing[:4]
    ]
    if not gaps:
        gaps = ["No missing required skills were reported."]

    questions = []
    for skill in matched[:2]:
        questions.append(
            f"Describe a project where you used {skill}. What was your role and what did you learn?"
        )
    for skill in missing[:2]:
        questions.append(
            f"This role uses {skill}. How would you get up to speed on it quickly?"
        )
    questions.extend([
        "Walk me through the project you are most proud of and the technical decisions you made.",
        "How do you debug a problem you have never seen before?",
        "Tell me about a time you worked in a team to meet a deadline.",
    ])

    return {
        "summary": summary,
        "strengths": strengths[:4],
        "gaps": gaps[:4],
        "interview_questions": questions[:5],
    }


@app.route("/api/ai/candidate-insights", methods=["POST"])
def candidate_insights():
    data = request.get_json(silent=True) or {}
    email = (data.get("candidate_email") or "").strip()
    job_title = (data.get("job_title") or "").strip()

    if not email or not job_title:
        return jsonify({
            "success": False,
            "message": "Candidate email and job title are required."
        }), 400

    db_client = None
    try:
        db_client = get_database()
        record = db_client[DATABASE_NAME]["candidate_matches"].find_one({
            "candidate_email": email,
            "job_title": job_title
        })
    except PyMongoError:
        app.logger.exception("Could not load candidate for insights")
        return jsonify({
            "success": False,
            "message": "Unable to load the candidate record."
        }), 500
    finally:
        if db_client is not None:
            db_client.close()

    if not record:
        return jsonify({
            "success": False,
            "message": "Candidate record not found."
        }), 404

    insights = build_candidate_insights(
        record.get("job_title", ""),
        record.get("skill_match_score_percent", 0),
        record.get("matched_skills", []),
        record.get("missing_skills", []),
    )

    return jsonify({"success": True, "insights": insights}), 200

import_lock = threading.Lock()


@app.route("/api/resumes/import", methods=["POST"])
def import_resumes():
    if not import_lock.acquire(blocking=False):
        return jsonify({
            "success": True, "busy": True,
            "added": [], "skipped": [], "failed": []
        }), 200

    try:
        from resume_importer import import_new_resumes
        summary = import_new_resumes()
        return jsonify({"success": True, **summary}), 200
    except Exception:
        app.logger.exception("Resume import failed")
        return jsonify({
            "success": False,
            "message": "Could not import resumes. Check the Flask terminal for details."
        }), 500
    finally:
        import_lock.release()


@app.route("/api/resumes/upload", methods=["POST"])
def upload_resumes():
    files = request.files.getlist("resumes")

    if not files:
        return jsonify({
            "success": False,
            "message": "No files were uploaded."
        }), 400

    RESUME_FOLDER.mkdir(exist_ok=True)
    saved = []
    rejected = []

    for file in files:
        original = secure_filename(file.filename or "")

        if not original.lower().endswith(".pdf"):
            rejected.append({
                "file": file.filename or "unnamed file",
                "reason": "Only PDF files are accepted."
            })
            continue

        header = file.stream.read(5)
        file.stream.seek(0)
        if header != b"%PDF-":
            rejected.append({
                "file": original,
                "reason": "This file is not a valid PDF."
            })
            continue

        target = RESUME_FOLDER / original
        counter = 1
        while target.exists():
            target = RESUME_FOLDER / f"{Path(original).stem}-{counter}.pdf"
            counter += 1

        file.save(target)
        saved.append(target.name)

    if not saved:
        return jsonify({
            "success": False,
            "message": "None of the files could be accepted.",
            "rejected": rejected
        }), 400

    with import_lock:
        try:
            from resume_importer import import_new_resumes
            summary = import_new_resumes()
        except Exception:
            app.logger.exception("Resume import after upload failed")
            return jsonify({
                "success": False,
                "message": "Files were saved but could not be processed. Check the Flask terminal."
            }), 500

    # Remove uploads that were duplicates or unreadable, so they don't pile up.
    for item in summary["skipped"] + summary["failed"]:
        if item["file"] in saved:
            (RESUME_FOLDER / item["file"]).unlink(missing_ok=True)

    return jsonify({
        "success": True,
        "saved": saved,
        "rejected": rejected,
        **summary
    }), 200


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    client = None

    try:
        client = get_database()
        records = list(client[DATABASE_NAME]["jobs"].find({}))

        jobs = [
            {
                "job_id": str(record.get("job_id", record["_id"])),
                "job_title": record.get("job_title", ""),
                "required_skills": record.get("required_skills", []),
            }
            for record in records
        ]

        return jsonify({"success": True, "jobs": jobs}), 200

    except PyMongoError:
        app.logger.exception("Could not retrieve jobs")
        return jsonify({
            "success": False,
            "message": "Unable to retrieve job positions."
        }), 500

    finally:
        if client is not None:
            client.close()


@app.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.get_json(silent=True) or {}

    title = (data.get("job_title") or "").strip()
    raw_skills = data.get("required_skills")

    if not title or len(title) > 80:
        return jsonify({
            "success": False,
            "message": "Enter a job title (up to 80 characters)."
        }), 400

    if not isinstance(raw_skills, list):
        return jsonify({
            "success": False,
            "message": "Required skills must be a list."
        }), 400

    skills = []
    seen = set()
    for item in raw_skills:
        skill = str(item).strip()
        if skill and len(skill) <= 40 and skill.casefold() not in seen:
            seen.add(skill.casefold())
            skills.append(skill)

    if not skills:
        return jsonify({
            "success": False,
            "message": "Add at least one required skill."
        }), 400

    if len(skills) > 20:
        return jsonify({
            "success": False,
            "message": "A position can have up to 20 required skills."
        }), 400

    client = None
    try:
        client = get_database()
        jobs = client[DATABASE_NAME]["jobs"]

        existing = jobs.find_one({
            "job_title": {"$regex": f"^{re.escape(title)}$", "$options": "i"}
        })
        if existing:
            return jsonify({
                "success": False,
                "message": "A position with this title already exists."
            }), 409

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        jobs.insert_one({
            "job_id": f"job-{slug}",
            "job_title": title,
            "required_skills": skills,
        })

    except PyMongoError:
        app.logger.exception("Could not save job position")
        return jsonify({
            "success": False,
            "message": "Unable to save the job position."
        }), 500
    finally:
        if client is not None:
            client.close()

    # Match every candidate against the new position.
    with import_lock:
        try:
            import database_candidate_matcher
            database_candidate_matcher.main()
        except Exception:
            app.logger.exception("Matching after new job failed")
            return jsonify({
                "success": False,
                "message": "Position saved, but matching failed. Check the Flask terminal."
            }), 500

    return jsonify({"success": True, "message": "Position added."}), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)

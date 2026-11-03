from collections import defaultdict
from pathlib import Path
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parent / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
APPLY = "--apply" in sys.argv

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
collection = client["recruitment_system"]["interviews"]

# Group every interview by candidate email
by_person = defaultdict(list)
for doc in collection.find({}):
    email = (doc.get("candidate_email") or "").strip().lower()
    by_person[email].append(doc)

to_delete = []
for email, docs in by_person.items():
    # Latest = latest date, then latest time, then most recently saved
    docs.sort(key=lambda d: (d.get("date", ""), d.get("time", ""), d["_id"]))
    keep, extras = docs[-1], docs[:-1]

    print(f"{email}: keeping {keep.get('date')} {keep.get('time')} "
          f"({keep.get('status', 'Scheduled')}), removing {len(extras)} older")
    to_delete.extend(d["_id"] for d in extras)

if not to_delete:
    print("Nothing to remove.")
elif APPLY:
    result = collection.delete_many({"_id": {"$in": to_delete}})
    print(f"\nDeleted {result.deleted_count} interview(s).")
else:
    print(f"\nPreview only. {len(to_delete)} interview(s) would be deleted.")
    print("Run again with --apply to delete them.")

client.close()
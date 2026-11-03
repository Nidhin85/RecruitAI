
def calculate_match(candidate_skills, required_skills):
    matched_skills = []

    for skill in required_skills:
        if skill.lower() in [s.lower() for s in candidate_skills]:
            matched_skills.append(skill)

    if len(required_skills) == 0:
        return 0, matched_skills

    score = len(matched_skills) / len(required_skills) * 100

    return score, matched_skills


# Sample candidate information
candidate = {
    "name": "Arun",
    "email": "arun@example.com",
    "experience": 2,
    "skills": ["Python", "Flask", "SQL"]
}

# Skills required by the job
required_skills = ["Python", "Flask", "MongoDB", "SQL"]

# Calculate the match
score, matched_skills = calculate_match(
    candidate["skills"],
    required_skills
)

# Display candidate information
print("===== RESUME SCREENING RESULT =====")
print("Candidate:", candidate["name"])
print("Email:", candidate["email"])
print("Experience:", candidate["experience"], "years")
print("Candidate skills:", candidate["skills"])
print("Matched skills:", matched_skills)
print("Missing skills:", [
    skill for skill in required_skills
    if skill.lower() not in [
        s.lower() for s in candidate["skills"]
    ]
])
print("Match score:", round(score, 2), "%")

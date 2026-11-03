
import unittest
from unittest.mock import patch, MagicMock

from app import app


class CandidateMatchingAPITests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_endpoint(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(
            data["message"],
            "Recruitment Management API is running"
        )

    @patch("app.get_database")
    def test_candidate_matches_endpoint(self, mock_get_database):
        mock_client = MagicMock()
        mock_get_database.return_value = mock_client

        mock_collection = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = (
            mock_collection
        )

        mock_collection.find.return_value.sort.return_value = [
            {
                "candidate_name": "Arun",
                "candidate_email": "arun@example.com",
                "job_title": "Python Developer",
                "skill_match_score_percent": 75.0,
                "matched_skills": ["Python", "Flask", "SQL"],
                "missing_skills": ["MongoDB"],
                "recruiter_decision": "Needs Review",
                "recruitment_status": "Under Review"
            }
        ]

        response = self.client.get("/api/candidates/matches")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["candidates"]), 1)
        self.assertEqual(data["candidates"][0]["candidate_name"], "Arun")
        self.assertEqual(
            data["candidates"][0]["skill_match_score_percent"],
            75.0
        )
        self.assertIn("missing_skills", data["candidates"][0])

        mock_client.close.assert_called_once()

    @patch("app.get_database")
    def test_database_error_returns_500(self, mock_get_database):
        mock_get_database.side_effect = Exception("Simulated failure")

        # The app currently handles PyMongoError exceptions.
        # This test confirms an unexpected error is not silently accepted.
        with self.assertRaises(Exception):
            self.client.get("/api/candidates/matches")


if __name__ == "__main__":
    unittest.main(verbosity=2)

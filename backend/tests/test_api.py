import unittest

from fastapi.testclient import TestClient

from app.main import app


class DispatchApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_reports_database_connection(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"], "connected")

    def test_jobs_require_authentication(self):
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 401)

    def test_admin_can_login_and_read_loads(self):
        login = self.client.post("/api/auth/login", json={"email": "admin@dispatchhub.local", "password": "admin123"})
        self.assertEqual(login.status_code, 200)
        token = login.json()["access_token"]
        loads = self.client.get("/api/jobs", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(loads.status_code, 200)
        self.assertIsInstance(loads.json(), list)


if __name__ == "__main__":
    unittest.main()

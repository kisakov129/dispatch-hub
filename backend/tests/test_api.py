import unittest
from uuid import uuid4

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

    def _admin_headers(self):
        login = self.client.post("/api/auth/login", json={"email": "admin@dispatchhub.local", "password": "admin123"})
        self.assertEqual(login.status_code, 200)
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    def test_load_assignment_lifecycle_and_driver_availability(self):
        headers = self._admin_headers()
        suffix = uuid4().hex[:8]
        driver_id = None
        job_ids = []
        try:
            driver = self.client.post("/api/drivers", headers=headers, json={"name": f"Test Driver {suffix}", "phone": "2145550199", "availability": "Available"})
            self.assertEqual(driver.status_code, 201)
            driver_id = driver.json()["id"]

            payload = {"customer": f"Test Customer {suffix}", "pickup": "Dallas, TX", "delivery": "Austin, TX", "date": "2026-11-06", "priority": "High"}
            first_job = self.client.post("/api/jobs", headers=headers, json=payload)
            second_job = self.client.post("/api/jobs", headers=headers, json={**payload, "customer": f"Second Customer {suffix}"})
            self.assertEqual(first_job.status_code, 201)
            self.assertEqual(second_job.status_code, 201)
            job_ids = [first_job.json()["id"], second_job.json()["id"]]

            assigned = self.client.post(f"/api/jobs/{job_ids[0]}/assign", headers=headers, json={"driver_id": driver_id})
            self.assertEqual(assigned.status_code, 200)
            self.assertEqual(assigned.json()["status"], "Active")
            self.assertEqual(assigned.json()["driver"], f"Test Driver {suffix}")

            unavailable = self.client.post(f"/api/jobs/{job_ids[1]}/assign", headers=headers, json={"driver_id": driver_id})
            self.assertEqual(unavailable.status_code, 409)

            completed = self.client.put(f"/api/dispatches/{job_ids[0]}/status", headers=headers, json={"status": "Completed"})
            self.assertEqual(completed.status_code, 200)
            self.assertEqual(completed.json()["status"], "Completed")
        finally:
            for job_id in job_ids:
                self.client.delete(f"/api/jobs/{job_id}", headers=headers)
            if driver_id:
                self.client.delete(f"/api/drivers/{driver_id}", headers=headers)

    def test_reports_summary_has_operational_metrics(self):
        headers = self._admin_headers()
        response = self.client.get("/api/reports/summary", headers=headers)
        self.assertEqual(response.status_code, 200)
        report = response.json()
        for key in ("total_loads", "completed_loads", "active_loads", "pending_loads", "unassigned_loads", "completion_rate", "driver_workload"):
            self.assertIn(key, report)
        self.assertIsInstance(report["driver_workload"], list)


if __name__ == "__main__":
    unittest.main()

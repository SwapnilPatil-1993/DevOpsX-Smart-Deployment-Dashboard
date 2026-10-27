import os
import tempfile
import unittest
from unittest.mock import patch

import app as devopsx


class DevOpsXAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = devopsx.DB_PATH
        devopsx.DB_PATH = os.path.join(self.temp_dir.name, "test_devopsx.db")
        devopsx.app.config.update(TESTING=True)
        devopsx.init_db()
        self.client = devopsx.app.test_client()

    def tearDown(self):
        devopsx.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_dashboard_loads_with_demo_records(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Deployment Control Center", response.data)
        self.assertIn(b"Campus Portal", response.data)

    def test_health_endpoint_returns_ok(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "service": "DevOpsX", "database": "sqlite"})

    def test_health_endpoint_reports_database_failure(self):
        with patch.object(devopsx, "db_connection", side_effect=RuntimeError("database unavailable")):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {
            "status": "error", "service": "DevOpsX", "database": "sqlite"
        })

    def test_add_deployment_record(self):
        response = self.client.post("/deployments/new", data={
            "project_name": "Test Project",
            "repository_url": "https://github.com/example/test-project",
            "environment": "Development",
            "status": "Queued",
            "notes": "Automated test"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Project", response.data)
        self.assertIn(b"Deployment record added.", response.data)

    def test_reject_invalid_status(self):
        response = self.client.post("/deployments/new", data={
            "project_name": "Test Project",
            "repository_url": "https://github.com/example/test-project",
            "environment": "Development",
            "status": "Unknown"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please select a valid environment and status.", response.data)
        self.assertNotIn(b"Unknown</span>", response.data)

    def test_delete_deployment_record(self):
        with devopsx.get_db() as conn:
            row = conn.execute(
                "SELECT id FROM deployments WHERE project_name = ?",
                ("Campus Portal",)
            ).fetchone()
        self.assertIsNotNone(row)
        response = self.client.post(
            f"/deployments/{row['id']}/delete",
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Campus Portal", response.data)
        self.assertIn(b"Deployment record deleted.", response.data)


if __name__ == "__main__":
    unittest.main()

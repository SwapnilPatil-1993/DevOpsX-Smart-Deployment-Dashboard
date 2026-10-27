import os
import re
import tempfile
import unittest
from unittest.mock import patch

import app as devopsx


class DevOpsXAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = devopsx.DB_PATH
        self.original_admin_username = devopsx.ADMIN_USERNAME
        self.original_admin_password = devopsx.ADMIN_PASSWORD
        devopsx.DB_PATH = os.path.join(self.temp_dir.name, "test_devopsx.db")
        devopsx.ADMIN_USERNAME = "test-admin"
        devopsx.ADMIN_PASSWORD = "test-password"
        devopsx.app.config.update(TESTING=True)
        devopsx.init_db()
        self.client = devopsx.app.test_client()

    def tearDown(self):
        devopsx.DB_PATH = self.original_db_path
        devopsx.ADMIN_USERNAME = self.original_admin_username
        devopsx.ADMIN_PASSWORD = self.original_admin_password
        self.temp_dir.cleanup()

    def csrf_token(self, response=None):
        if response is None:
            response = self.client.get("/login")
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        self.assertIsNotNone(match, "CSRF token should be present in the form")
        return match.group(1).decode()

    def login(self):
        response = self.client.get("/login")
        token = self.csrf_token(response)
        return self.client.post("/login", data={
            "csrf_token": token,
            "username": "test-admin",
            "password": "test-password",
        }, follow_redirects=True)

    def test_dashboard_requires_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_login_page_loads(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back", response.data)

    def test_valid_login_opens_dashboard(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Deployment Control Center", response.data)

    def test_invalid_login_is_rejected(self):
        token = self.csrf_token()
        response = self.client.post("/login", data={
            "csrf_token": token,
            "username": "test-admin",
            "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    def test_csrf_token_is_required_for_mutations(self):
        self.login()
        response = self.client.post("/deployments/new", data={
            "project_name": "Should not be created",
            "repository_url": "https://github.com/example/project",
            "environment": "Development",
            "status": "Queued",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"CSRF token", response.data)

    def test_dashboard_loads_with_demo_records(self):
        self.login()
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
        self.login()
        token = self.csrf_token(self.client.get("/"))
        response = self.client.post("/deployments/new", data={
            "csrf_token": token,
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
        self.login()
        token = self.csrf_token(self.client.get("/"))
        response = self.client.post("/deployments/new", data={
            "csrf_token": token,
            "project_name": "Test Project",
            "repository_url": "https://github.com/example/test-project",
            "environment": "Development",
            "status": "Unknown"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please select a valid environment and status.", response.data)
        self.assertNotIn(b"Unknown</span>", response.data)

    def test_delete_deployment_record(self):
        self.login()
        token = self.csrf_token(self.client.get("/"))
        with devopsx.get_db() as conn:
            row = conn.execute(
                "SELECT id FROM deployments WHERE project_name = ?",
                ("Campus Portal",)
            ).fetchone()
        self.assertIsNotNone(row)
        response = self.client.post(
            f"/deployments/{row['id']}/delete",
            data={"csrf_token": token},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Campus Portal", response.data)
        self.assertIn(b"Deployment record deleted.", response.data)

    def test_logout_clears_authentication(self):
        self.login()
        token = self.csrf_token(self.client.get("/"))
        response = self.client.post("/logout", data={"csrf_token": token}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sign in", response.data)
        self.assertEqual(self.client.get("/").status_code, 302)


if __name__ == "__main__":
    unittest.main()

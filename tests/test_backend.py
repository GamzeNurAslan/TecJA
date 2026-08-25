from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGE_ROOT = PROJECT_ROOT / ".codex-stage"
SOURCE_DB = STAGE_ROOT / "tenant" / "test-isolation.db"

if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from fastapi.testclient import TestClient

from backend.app import config, database, main
class BackendApiTests(unittest.TestCase):
    """Integration tests for the main TecJA API workflows.

    Each test class run uses a temporary copy of the staged tenant database,
    so the user's working database and live simulation records are untouched.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory(prefix="tecja-tests-")
        cls.test_db = Path(cls.temp_dir.name) / "tecja-test.db"
        shutil.copy2(SOURCE_DB, cls.test_db)

        database.DATABASE_PATH = cls.test_db
        config.DATABASE_PATH = cls.test_db

        cls.client_context = TestClient(main.app)
        cls.client = cls.client_context.__enter__()

        admin_response = cls.client.post(
            "/api/auth/login",
            json={
                "email": "admin@tecja.com",
                "password": "admin123",
            },
        )
        if admin_response.status_code != 200:
            raise AssertionError(
                "Admin test login failed: "
                f"{admin_response.status_code} {admin_response.text}"
            )
        cls.admin_token = admin_response.json()["access_token"]

        analyst_response = cls.client.post(
            "/api/auth/login",
            json={
                "email": "analyst@tecja.com",
                "password": "analyst123",
            },
        )
        if analyst_response.status_code != 200:
            raise AssertionError(
                "Analyst test login failed: "
                f"{analyst_response.status_code} {analyst_response.text}"
            )
        cls.analyst_token = analyst_response.json()["access_token"]

        second_analyst_response = cls.client.post(
            "/api/auth/login",
            json={
                "email": "analyst2@tecja.com",
                "password": "analyst2123",
            },
        )
        if second_analyst_response.status_code != 200:
            raise AssertionError(
                "Second analyst test login failed: "
                f"{second_analyst_response.status_code} "
                f"{second_analyst_response.text}"
            )
        cls.second_analyst_token = second_analyst_response.json()[
            "access_token"
        ]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        cls.temp_dir.cleanup()

    @staticmethod
    def headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def test_login_and_protected_endpoint(self) -> None:
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 401)

        login = self.client.post(
            "/api/auth/login",
            json={
                "email": "admin@tecja.com",
                "password": "wrong-password",
            },
        )
        self.assertEqual(login.status_code, 401)

        login = self.client.post(
            "/api/auth/login",
            json={
                "email": "admin@tecja.com",
                "password": "admin123",
            },
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["user"]["role"], "admin")
        self.assertTrue(login.json()["access_token"])

    def test_dashboard_summary(self) -> None:
        response = self.client.get(
            "/api/summary",
            headers=self.headers(self.admin_token),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload["total_customers"], 5001)
        self.assertGreater(payload["total_journey_events"], 0)
        self.assertGreater(payload["total_tickets"], 0)
        self.assertIn("average_resolution_hours", payload)

    def test_customer_search_and_pagination(self) -> None:
        first_page = self.client.get(
            "/api/customer-metrics?limit=5&offset=0",
            headers=self.headers(self.admin_token),
        )
        self.assertEqual(first_page.status_code, 200)
        payload = first_page.json()
        self.assertLessEqual(payload["count"], 5)
        self.assertEqual(payload["page"], 1)
        self.assertGreater(payload["total_pages"], 1)

        customer_id = payload["items"][0]["customer_id"]
        search = self.client.get(
            "/api/customer-metrics?limit=5&search=" + customer_id,
            headers=self.headers(self.admin_token),
        )
        self.assertEqual(search.status_code, 200)
        search_payload = search.json()
        self.assertGreaterEqual(search_payload["total_count"], 1)
        self.assertEqual(search_payload["items"][0]["customer_id"], customer_id)

        second_page = self.client.get(
            "/api/customer-metrics?limit=5&offset=5",
            headers=self.headers(self.admin_token),
        )
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(second_page.json()["page"], 2)

    def test_provider_data_isolation(self) -> None:
        first_provider = self.client.get(
            "/api/customer-metrics?limit=100",
            headers=self.headers(self.analyst_token),
        )
        second_provider = self.client.get(
            "/api/customer-metrics?limit=100",
            headers=self.headers(self.second_analyst_token),
        )
        self.assertEqual(first_provider.status_code, 200)
        self.assertEqual(second_provider.status_code, 200)

        first_payload = first_provider.json()
        second_payload = second_provider.json()
        self.assertEqual(first_payload["total_count"], 5000)
        self.assertEqual(second_payload["total_count"], 1)
        self.assertTrue(
            all(
                item["provider_id"] == "ISP001"
                for item in first_payload["items"]
            )
        )
        self.assertTrue(
            all(
                item["provider_id"] == "ISP002"
                for item in second_payload["items"]
            )
        )

        risk_summary = self.client.get(
            "/api/risk-summary",
            headers=self.headers(self.second_analyst_token),
        )
        self.assertEqual(risk_summary.status_code, 200)
        self.assertLessEqual(len(risk_summary.json()["items"]), 3)

        providers = self.client.get(
            "/api/providers",
            headers=self.headers(self.admin_token),
        )
        self.assertEqual(providers.status_code, 200)
        provider_ids = {item["provider_id"] for item in providers.json()["items"]}
        self.assertTrue({"ISP001", "ISP002"}.issubset(provider_ids))

    def test_simulation_event_is_persistent(self) -> None:
        before = self.client.get(
            "/api/summary",
            headers=self.headers(self.admin_token),
        ).json()
        tick = self.client.post(
            "/api/simulation/tick",
            headers=self.headers(self.admin_token),
        )
        self.assertEqual(tick.status_code, 200)
        self.assertEqual(tick.json()["changes"]["new_journey_event"], 1)
        self.assertEqual(tick.json()["changes"]["new_ticket"], 1)

        after = self.client.get(
            "/api/summary",
            headers=self.headers(self.admin_token),
        ).json()
        self.assertEqual(
            after["total_journey_events"],
            before["total_journey_events"] + 1,
        )
        self.assertEqual(
            after["total_tickets"],
            before["total_tickets"] + 1,
        )

    def test_report_generation_and_email_validation(self) -> None:
        invalid_email = self.client.post(
            "/api/reports/email",
            headers=self.headers(self.admin_token),
            json={"recipient": "not-an-email"},
        )
        self.assertEqual(invalid_email.status_code, 400)

        with patch(
            "backend.app.api.routes.build_report_pdf",
            return_value=b"%PDF-test",
        ), patch(
            "backend.app.api.routes.send_report_email"
        ) as send_email:
            response = self.client.post(
                "/api/reports/email",
                headers=self.headers(self.admin_token),
                json={"recipient": "test@example.com"},
            )

        self.assertEqual(response.status_code, 200)
        send_email.assert_called_once()


if __name__ == "__main__":
    unittest.main()

"""test admin api"""
from json import loads

from django.shortcuts import reverse
from django.test import TestCase

from authentik import __version__
from authentik.core.models import Group, User


class TestAdminAPI(TestCase):
    """test admin api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="test-user")
        self.group = Group.objects.create(name="superusers", is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    def test_tasks(self):
        """Test Task API"""
        response = self.client.get(reverse("authentik_api:admin_system_tasks-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertTrue(
            any([task["task_name"] == "clean_expired_models" for task in body])
        )

    def test_tasks_retry(self):
        """Test Task API (retry)"""
        response = self.client.post(
            reverse(
                "authentik_api:admin_system_tasks-retry",
                kwargs={"pk": "clean_expired_models"},
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertTrue(body["successful"])

    def test_tasks_retry_404(self):
        """Test Task API (retry, 404)"""
        response = self.client.post(
            reverse(
                "authentik_api:admin_system_tasks-retry",
                kwargs={"pk": "qwerqewrqrqewrqewr"},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_version(self):
        """Test Version API"""
        response = self.client.get(reverse("authentik_api:admin_version-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["version_current"], __version__)

    def test_workers(self):
        """Test Workers API"""
        response = self.client.get(reverse("authentik_api:admin_workers-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["pagination"]["count"], 0)

    def test_metrics(self):
        """Test metrics API"""
        response = self.client.get(reverse("authentik_api:admin_metrics-list"))
        self.assertEqual(response.status_code, 200)

"""
Common test helpers — authentication, role-based API client setup.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from apps.partners.models import SubCenter, SystemUser
from tests.factories import SubCenterFactory


class BaseAPITestCase(TestCase):
    """Base class for API tests — provides authenticated client per role."""

    def setUp(self):
        super().setUp()
        self.center_a = SubCenterFactory(center_code='TEST-A')
        self.center_b = SubCenterFactory(center_code='TEST-B')

    def _make_user(self, role, sub_center=None, username=None):
        """Create a Django User + SystemUser with given role."""
        username = username or f'{role}_{sub_center.center_code if sub_center else "global"}'
        user = User.objects.create_user(username=username, password='testpass123', email=f'{username}@test.com')
        su = SystemUser.objects.create(
            user=user,
            sub_center=sub_center,
            role=role,
            email=user.email,
        )
        token = Token.objects.create(user=user)
        return user, su, token

    def _client(self, role, sub_center=None):
        """Return APIClient authenticated as given role."""
        user, su, token = self._make_user(role, sub_center)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        client.user = user
        client.systemuser = su
        return client

    def super_admin_client(self):
        return self._client(SystemUser.ROLE_SUPER_ADMIN, sub_center=None)

    def academic_head_client(self):
        return self._client(SystemUser.ROLE_ACADEMIC_HEAD, sub_center=None)

    def counselor_client(self, sub_center=None):
        return self._client(SystemUser.ROLE_COUNSELOR, sub_center or self.center_a)

    def finance_client(self, sub_center=None):
        return self._client(SystemUser.ROLE_FINANCE, sub_center or self.center_a)

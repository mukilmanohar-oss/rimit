import json
import pytest
from rest_framework import status
from django.contrib.auth.models import User
from apps.partners.models import SystemUser
from tests.base import BaseAPITestCase
from tests.factories import SubCenterFactory

@pytest.mark.django_db
class TestSubCenterAdminSystemUsers(BaseAPITestCase):
    """
    Tests covering requirements for Sub-Center Admin accessing the System Users API.
    """

    def setUp(self):
        super().setUp()
        self.subcenter_admin_a_client = self._client(SystemUser.ROLE_SUBCENTER, self.center_a)
        self.subcenter_admin_b_client = self._client(SystemUser.ROLE_SUBCENTER, self.center_b)

        # Create users under center A
        self.user_a1, _, _ = self._make_user(SystemUser.ROLE_COUNSELOR, self.center_a, 'counselor_a1')
        self.user_a2, _, _ = self._make_user(SystemUser.ROLE_FINANCE, self.center_a, 'finance_a2')

        # Create users under center B
        self.user_b1, _, _ = self._make_user(SystemUser.ROLE_COUNSELOR, self.center_b, 'counselor_b1')

        # Super admin users
        self.super_admin_user, _, _ = self._make_user(SystemUser.ROLE_SUPER_ADMIN, None, 'super_admin_user')

    def test_super_admin_receives_all_users(self):
        client = self.super_admin_client()
        resp = client.get('/api/v1/users')
        assert resp.status_code == status.HTTP_200_OK
        # Should return all users in the system (includes setup users + the ones created here)
        user_ids = [u['id'] for u in resp.data['results']]
        assert str(self.user_a1.systemuser.id) in user_ids
        assert str(self.user_b1.systemuser.id) in user_ids
        assert str(self.super_admin_user.systemuser.id) in user_ids

    def test_subcenter_admin_receives_only_own_subcenter_users(self):
        resp = self.subcenter_admin_a_client.get('/api/v1/users')
        assert resp.status_code == status.HTTP_200_OK
        user_ids = [u['id'] for u in resp.data['results']]

        # Must return center A users
        assert str(self.user_a1.systemuser.id) in user_ids
        assert str(self.user_a2.systemuser.id) in user_ids

        # Excludes center B users
        assert str(self.user_b1.systemuser.id) not in user_ids
        # Excludes Super Admin users
        assert str(self.super_admin_user.systemuser.id) not in user_ids

    def test_subcenter_admin_create_user_forces_own_subcenter(self):
        resp = self.subcenter_admin_a_client.post('/api/v1/users', {
            'username': 'new_subcenter_admin_a3',
            'password': 'testpass123',
            'email': 'subcenter_a3@test.com',
            'phone': '+919999999999',
            'role': SystemUser.ROLE_SUBCENTER,
            'sub_center': str(self.center_b.id) # Attempt to assign to center B
        })
        assert resp.status_code == status.HTTP_201_CREATED
        system_user_id = resp.data['id']
        su = SystemUser.objects.get(id=system_user_id)
        # Forced to center A
        assert su.sub_center == self.center_a

    def test_subcenter_admin_cannot_create_counselor_or_finance_or_academic_head(self):
        for role in (SystemUser.ROLE_COUNSELOR, SystemUser.ROLE_FINANCE, SystemUser.ROLE_ACADEMIC_HEAD):
            resp = self.subcenter_admin_a_client.post('/api/v1/users', {
                'username': f'new_{role}',
                'password': 'testpass123',
                'email': f'{role.replace("_", "")}@test.com',
                'role': role,
                'sub_center': str(self.center_a.id)
            })
            assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)

    def test_subcenter_admin_without_mapping_cannot_create_user(self):
        client = self._client(SystemUser.ROLE_SUBCENTER, None)
        assert client.systemuser.sub_center is None

        resp = client.post('/api/v1/users', {
            'username': 'attacker_unscoped',
            'password': 'testpass123',
            'email': 'unscoped@test.com',
            'role': SystemUser.ROLE_SUBCENTER,
        })
        assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)

    def test_subcenter_admin_cannot_create_super_admin(self):
        resp = self.subcenter_admin_a_client.post('/api/v1/users', {
            'username': 'attacker_sa',
            'password': 'testpass123',
            'email': 'attacker_sa@test.com',
            'role': SystemUser.ROLE_SUPER_ADMIN,
            'sub_center': str(self.center_a.id)
        })
        # Should fail with bad request / permission denied
        assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)

    def test_subcenter_admin_cannot_update_role_to_super_admin(self):
        # Attempt to elevate a counselor to super admin
        resp = self.subcenter_admin_a_client.patch(f'/api/v1/users/{self.user_a1.systemuser.id}', {
            'role': SystemUser.ROLE_SUPER_ADMIN
        })
        assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)

    def test_subcenter_admin_cannot_view_other_center_user(self):
        resp = self.subcenter_admin_a_client.get(f'/api/v1/users/{self.user_b1.systemuser.id}')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_subcenter_admin_cannot_edit_other_center_user(self):
        resp = self.subcenter_admin_a_client.patch(f'/api/v1/users/{self.user_b1.systemuser.id}', {
            'phone': '+910000000000'
        })
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_subcenter_admin_cannot_delete_other_center_user(self):
        resp = self.subcenter_admin_a_client.delete(f'/api/v1/users/{self.user_b1.systemuser.id}')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthorized_roles_receive_403(self):
        counselor_client = self.counselor_client(self.center_a)
        resp = counselor_client.get('/api/v1/users')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

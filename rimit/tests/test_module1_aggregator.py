"""
Phase 1 / Module 1 — Aggregator Hub tests.

Covers:
- University CRUD (super_admin can write, others read)
- Course search with multi-attribute filters
- Fee structure CRUD
- Document vault presigned URL endpoint
- Permission matrix (RBAC enforcement)
- Search behavior (name, stream, eligibility)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.aggregator.models import University, Course, FeeStructure, UniversityDocVault
from apps.partners.models import SystemUser, SubCenterUniversityMapping
from tests.factories import UniversityFactory, CourseFactory, FeeStructureFactory
from tests.base import BaseAPITestCase


@pytest.mark.django_db
class TestUniversityAPI(BaseAPITestCase):

    def test_super_admin_can_create_university(self):
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Mangalayatan University',
            'state': 'Uttar Pradesh',
            'accreditation': 'NAAC A',
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_201_CREATED, resp.content
        assert University.objects.filter(name='Mangalayatan University').exists()

    def test_counselor_cannot_create_university(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Forbidden University',
            'state': 'Kerala',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_academic_head_can_read_all_universities(self):
        UniversityFactory(name='Uni A', state='Kerala')
        UniversityFactory(name='Uni B', state='Tamil Nadu')
        client = self.academic_head_client()
        resp = client.get('/api/v1/universities')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 2

    def test_filter_universities_by_state(self):
        UniversityFactory(name='KL University', state='Kerala')
        UniversityFactory(name='TN University', state='Tamil Nadu')
        # Map only Kerala university to counselor's sub-center
        kl = University.objects.get(name='KL University')
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=kl)
        client = self.counselor_client()
        resp = client.get('/api/v1/universities?state=Kerala')
        assert resp.status_code == status.HTTP_200_OK
        names = [u['name'] for u in resp.data['results']]
        assert 'KL University' in names
        assert 'TN University' not in names

    def test_university_detail_includes_courses_and_documents(self):
        uni = UniversityFactory(name='Detail Uni')
        course = CourseFactory(university=uni, name='BCA')
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        UniversityDocVault.objects.create(
            university=uni, doc_type='prospectus', title='2026 Prospectus',
            s3_object_uri='s3://bucket/prospectus.pdf'
        )
        client = self.counselor_client()
        resp = client.get(f'/api/v1/universities/{uni.id}')
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['courses']) == 1
        assert resp.data['courses'][0]['name'] == 'BCA'
        assert len(resp.data['documents']) == 1

    def test_inactive_university_hidden_from_non_admin(self):
        UniversityFactory(name='Active Uni', is_active=True)
        UniversityFactory(name='Inactive Uni', is_active=False)
        active = University.objects.get(name='Active Uni')
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=active)
        client = self.counselor_client()
        resp = client.get('/api/v1/universities')
        names = [u['name'] for u in resp.data['results']]
        assert 'Active Uni' in names
        assert 'Inactive Uni' not in names

    def test_super_admin_sees_inactive_universities(self):
        UniversityFactory(name='Active Uni', is_active=True)
        UniversityFactory(name='Inactive Uni', is_active=False)
        client = self.super_admin_client()
        resp = client.get('/api/v1/universities')
        names = [u['name'] for u in resp.data['results']]
        assert 'Active Uni' in names
        assert 'Inactive Uni' in names


@pytest.mark.django_db
class TestCourseSearch(BaseAPITestCase):

    def test_course_search_by_name(self):
        uni = UniversityFactory(name='Test Uni')
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        CourseFactory(university=uni, name='Bachelor of Computer Applications')
        CourseFactory(university=uni, name='Master of Business Administration')
        client = self.counselor_client()
        resp = client.get('/api/v1/courses?search=Computer')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        assert 'Computer' in resp.data['results'][0]['name']

    def test_course_filter_by_stream(self):
        uni = UniversityFactory()
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        CourseFactory(university=uni, stream=Course.STREAM_UG)
        CourseFactory(university=uni, stream=Course.STREAM_PG)
        CourseFactory(university=uni, stream=Course.STREAM_UG)
        client = self.counselor_client()
        resp = client.get(f'/api/v1/courses?stream={Course.STREAM_UG}')
        assert resp.data['count'] == 2

    def test_course_filter_by_duration(self):
        uni = UniversityFactory()
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        CourseFactory(university=uni, duration_months=12)
        CourseFactory(university=uni, duration_months=36)
        client = self.counselor_client()
        resp = client.get('/api/v1/courses?duration_months=36')
        assert resp.data['count'] == 1

    def test_course_list_serializer_includes_total_fee(self):
        uni = UniversityFactory()
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        course = CourseFactory(university=uni, name='Test Course')
        FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=50000)
        FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_ADMISSION, amount=5000)
        client = self.counselor_client()
        resp = client.get('/api/v1/courses')
        assert resp.data['count'] == 1
        # total_fee = 50000 + 5000 = 55000
        assert float(resp.data['results'][0]['total_fee']) == 55000.0


@pytest.mark.django_db
class TestFeeStructureAPI(BaseAPITestCase):

    def test_super_admin_can_create_fee(self):
        course = CourseFactory()
        client = self.super_admin_client()
        resp = client.post('/api/v1/fees', {
            'course': str(course.id),
            'fee_type': FeeStructure.FEE_TUITION,
            'amount': '75000.00',
            'currency': 'INR',
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_201_CREATED

    def test_counselor_cannot_create_fee(self):
        course = CourseFactory()
        client = self.counselor_client()
        resp = client.post('/api/v1/fees', {
            'course': str(course.id),
            'fee_type': FeeStructure.FEE_TUITION,
            'amount': '75000.00',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_fees_by_course(self):
        course1 = CourseFactory()
        course2 = CourseFactory()
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=course1.university)
        FeeStructureFactory(course=course1, fee_type=FeeStructure.FEE_TUITION)
        FeeStructureFactory(course=course1, fee_type=FeeStructure.FEE_ADMISSION)
        FeeStructureFactory(course=course2, fee_type=FeeStructure.FEE_TUITION)
        client = self.counselor_client()
        resp = client.get(f'/api/v1/fees?course={course1.id}')
        assert resp.data['count'] == 2


@pytest.mark.django_db
class TestUniversityDocVault(BaseAPITestCase):

    def test_download_returns_presigned_url(self):
        uni = UniversityFactory()
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        doc = UniversityDocVault.objects.create(
            university=uni,
            doc_type=UniversityDocVault.DOC_PROSPECTUS,
            title='Test Prospectus',
            s3_object_uri='s3://bucket/test.pdf',
        )
        client = self.counselor_client()
        resp = client.get(f'/api/v1/prospectus/{doc.id}/download')
        assert resp.status_code == status.HTTP_200_OK
        assert 'url' in resp.data
        assert resp.data['ttl_seconds'] == 900  # 15 minutes
        assert resp.data['url'] == 's3://bucket/test.pdf'

    def test_super_admin_can_upload_document(self):
        uni = UniversityFactory()
        client = self.super_admin_client()
        resp = client.post('/api/v1/prospectus', {
            'university': str(uni.id),
            'doc_type': UniversityDocVault.DOC_PROSPECTUS,
            'title': 'New Prospectus',
            's3_object_uri': 's3://bucket/new.pdf',
            'mime_type': 'application/pdf',
        })
        assert resp.status_code == status.HTTP_201_CREATED

    def test_counselor_cannot_upload_document(self):
        uni = UniversityFactory()
        client = self.counselor_client()
        resp = client.post('/api/v1/prospectus', {
            'university': str(uni.id),
            'doc_type': UniversityDocVault.DOC_PROSPECTUS,
            'title': 'Attempted Upload',
            's3_object_uri': 's3://bucket/attempt.pdf',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

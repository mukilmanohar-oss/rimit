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
from apps.admissions.models import Enrollment
from apps.partners.models import SystemUser, SubCenter, SubCenterUniversityMapping
from tests.factories import UniversityFactory, CourseFactory, FeeStructureFactory, StudentFactory, IntakeSessionFactory, EnrollmentFactory
from tests.base import BaseAPITestCase

TEST_DEFAULT_SHARE_PERCENT = '50.00'


@pytest.mark.django_db
class TestUniversityAPI(BaseAPITestCase):

    def test_super_admin_can_create_university(self):
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Mangalayatan University',
            'state': 'Uttar Pradesh',
            'accreditation': 'NAAC A',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_201_CREATED, resp.content
        assert University.objects.filter(name='Mangalayatan University').exists()

    def test_counselor_cannot_create_university(self):
        client = self.counselor_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Forbidden University',
            'state': 'Kerala',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
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

    def test_create_unique_name_and_state_success(self):
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Amity University',
            'state': 'Kerala',
            'accreditation': 'UGC',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_201_CREATED

    def test_create_duplicate_name_same_state_failure(self):
        UniversityFactory(name='Amity University', state='Kerala')
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Amity University',
            'state': 'Kerala',
            'accreditation': 'UGC',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'A university with this name already exists in the selected state.' in str(resp.data)

    def test_create_duplicate_name_different_casing_same_state_failure(self):
        UniversityFactory(name='Amity University', state='Kerala')
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', {
            'name': 'amity university',
            'state': 'Kerala',
            'accreditation': 'UGC',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'A university with this name already exists in the selected state.' in str(resp.data)

    def test_create_same_name_different_state_success(self):
        UniversityFactory(name='Amity University', state='Kerala')
        client = self.super_admin_client()
        resp = client.post('/api/v1/universities', {
            'name': 'Amity University',
            'state': 'Karnataka',
            'accreditation': 'UGC',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
        })
        assert resp.status_code == status.HTTP_201_CREATED

    def test_update_keep_existing_values_success(self):
        uni = UniversityFactory(name='Amity University', state='Kerala')
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/universities/{uni.id}', {
            'accreditation': 'NAAC A++',
        })
        assert resp.status_code == status.HTTP_200_OK
        uni.refresh_from_db()
        assert uni.accreditation == 'NAAC A++'

    def test_update_rename_to_duplicate_in_same_state_failure(self):
        uni1 = UniversityFactory(name='Amity University', state='Kerala')
        uni2 = UniversityFactory(name='LPU', state='Kerala')
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/universities/{uni2.id}', {
            'name': 'AMITY UNIVERSITY',
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'A university with this name already exists in the selected state.' in str(resp.data)

    def test_update_rename_to_duplicate_in_different_state_success(self):
        uni1 = UniversityFactory(name='Amity University', state='Kerala')
        uni2 = UniversityFactory(name='LPU', state='Karnataka')
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/universities/{uni2.id}', {
            'name': 'Amity University',
        })
        assert resp.status_code == status.HTTP_200_OK

    def test_update_change_state_only_success(self):
        uni = UniversityFactory(name='Amity University', state='Kerala')
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/universities/{uni.id}', {
            'state': 'Karnataka',
        })
        assert resp.status_code == status.HTTP_200_OK
        uni.refresh_from_db()
        assert uni.state == 'Karnataka'

    def test_update_name_only_success(self):
        uni = UniversityFactory(name='Amity University', state='Kerala')
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/universities/{uni.id}', {
            'name': 'Amity New Name',
        })
        assert resp.status_code == status.HTTP_200_OK
        uni.refresh_from_db()
        assert uni.name == 'Amity New Name'

    def test_partial_patch_conflict_checks(self):
        UniversityFactory(name='Amity University', state='Kerala')
        uni2 = UniversityFactory(name='LPU', state='Karnataka')
        client = self.super_admin_client()

        # Update name only to conflict with another university in a different state (should succeed)
        resp1 = client.patch(f'/api/v1/universities/{uni2.id}', {
            'name': 'Amity University',
        })
        assert resp1.status_code == status.HTTP_200_OK

        # Update state only to conflict with another university of the same name (should fail)
        resp2 = client.patch(f'/api/v1/universities/{uni2.id}', {
            'state': 'Kerala',
        })
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'A university with this name already exists in the selected state.' in str(resp2.data)

    def test_edge_cases_whitespace_and_special_chars(self):
        uni = UniversityFactory(name='ABC University', state='Kerala')
        client = self.super_admin_client()

        # Leading/trailing spaces create
        resp = client.post('/api/v1/universities', {
            'name': ' ABC University ',
            'state': ' Kerala ',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # Unicode/Special chars create unique
        resp2 = client.post('/api/v1/universities', {
            'name': 'Universität-1!',
            'state': 'München',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
        })
        assert resp2.status_code == status.HTTP_201_CREATED

        # Duplicate Unicode
        resp3 = client.post('/api/v1/universities', {
            'name': 'universität-1!',
            'state': 'München',
            'default_university_share_percent': TEST_DEFAULT_SHARE_PERCENT,
        })
        assert resp3.status_code == status.HTTP_400_BAD_REQUEST

    def test_default_university_share_percent_mandatory(self):
        client = self.super_admin_client()
        # Missing field on create
        resp = client.post('/api/v1/universities', {
            'name': 'Test Mandatory Uni',
            'state': 'Kerala',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'default_university_share_percent' in resp.data

        # Explicitly null on create
        resp = client.post('/api/v1/universities', {
            'name': 'Test Mandatory Uni 2',
            'state': 'Kerala',
            'default_university_share_percent': None,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'default_university_share_percent' in resp.data

        # Explicitly null on update
        uni = UniversityFactory(name='Update Uni', state='Kerala')
        resp = client.patch(f'/api/v1/universities/{uni.id}', {
            'default_university_share_percent': None,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'default_university_share_percent' in resp.data

        # Value = 0 on create
        resp = client.post('/api/v1/universities', {
            'name': 'Test Mandatory Uni 3',
            'state': 'Kerala',
            'default_university_share_percent': 0,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'default_university_share_percent' in resp.data

        # Value < 0 on create
        resp = client.post('/api/v1/universities', {
            'name': 'Test Mandatory Uni 4',
            'state': 'Kerala',
            'default_university_share_percent': -5.50,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'default_university_share_percent' in resp.data

        # Value > 100 on create
        resp = client.post('/api/v1/universities', {
            'name': 'Test Mandatory Uni 5',
            'state': 'Kerala',
            'default_university_share_percent': 105.00,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'default_university_share_percent' in resp.data


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

    def test_course_creation_with_new_streams(self):
        uni = UniversityFactory()
        client = self.super_admin_client()

        # Test PG Diploma Course Creation
        resp_pgd = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Executive PG Diploma',
            'stream': 'PG Diploma',
            'duration_months': 12,
            'university_share_percent': '15.00',
            'eligibility_text': 'Graduation with 50%',
            'is_active': True,
        })
        assert resp_pgd.status_code == status.HTTP_201_CREATED, resp_pgd.content
        assert Course.objects.filter(name='Executive PG Diploma', stream='PG Diploma').exists()

        # Test Certification Course Creation
        resp_cert = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Cloud Computing Certification',
            'stream': 'Certification',
            'duration_months': 6,
            'university_share_percent': '10.00',
            'eligibility_text': '10+2',
            'is_active': True,
        })
        assert resp_cert.status_code == status.HTTP_201_CREATED, resp_cert.content
        assert Course.objects.filter(name='Cloud Computing Certification', stream='Certification').exists()

        # Test Invalid Stream Rejection
        resp_invalid = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Invalid Stream Course',
            'stream': 'Random Stream',
            'duration_months': 6,
            'university_share_percent': '10.00',
        })
        assert resp_invalid.status_code == status.HTTP_400_BAD_REQUEST

    def test_course_filter_by_new_streams(self):
        uni = UniversityFactory()
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        CourseFactory(university=uni, stream='PG Diploma', name='PGD 1')
        CourseFactory(university=uni, stream='Certification', name='Cert 1')
        CourseFactory(university=uni, stream=Course.STREAM_UG, name='UG 1')

        client = self.counselor_client()

        # Filter by PG Diploma
        resp_pgd = client.get('/api/v1/courses?stream=PG Diploma')
        assert resp_pgd.status_code == status.HTTP_200_OK
        assert resp_pgd.data['count'] == 1
        assert resp_pgd.data['results'][0]['name'] == 'PGD 1'

        # Filter by Certification
        resp_cert = client.get('/api/v1/courses?stream=Certification')
        assert resp_cert.status_code == status.HTTP_200_OK
        assert resp_cert.data['count'] == 1
        assert resp_cert.data['results'][0]['name'] == 'Cert 1'

    def test_course_university_share_percent_validation(self):
        uni = UniversityFactory()
        client = self.super_admin_client()

        # 1. Blank/None should be valid (stores NULL/blank)
        resp = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Valid Course 1',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'university_share_percent': None,
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED, resp.content
        assert resp.data['university_share_percent'] is None

        # 2. 0 should be invalid
        resp = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Invalid Course 0',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'university_share_percent': 0,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'university_share_percent' in resp.data

        # 3. 0.00 should be invalid
        resp = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Invalid Course 0.00',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'university_share_percent': 0.00,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'university_share_percent' in resp.data

        # 4. Negative values should be invalid
        resp = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Invalid Course Neg',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'university_share_percent': -5.00,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'university_share_percent' in resp.data

        # 5. Values > 100 should be invalid
        resp = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Invalid Course Over',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'university_share_percent': 105.00,
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'university_share_percent' in resp.data

        # 6. Valid percentage value should be accepted
        resp = client.post('/api/v1/courses', {
            'university': str(uni.id),
            'name': 'Valid Course 25',
            'stream': 'Undergraduate',
            'duration_months': 36,
            'university_share_percent': 25.00,
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED, resp.content
        assert float(resp.data['university_share_percent']) == 25.00


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

    def test_create_and_retrieve_new_fee_types(self):
        course = CourseFactory()
        client = self.super_admin_client()
        resp = client.post('/api/v1/fees', {
            'course': str(course.id),
            'fee_type': FeeStructure.FEE_COURSE,
            'amount': '50000.00',
            'currency': 'INR',
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=course.university)
        resp = client.post('/api/v1/fees', {
            'course': str(course.id),
            'fee_type': FeeStructure.FEE_REGISTRATION,
            'amount': '2000.00',
            'currency': 'INR',
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_201_CREATED
        client_counselor = self.counselor_client()
        resp = client_counselor.get('/api/v1/courses')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 1
        assert float(resp.data['results'][0]['total_fee']) == 52000.00

    def test_super_admin_can_patch_fee(self):
        course = CourseFactory()
        fee = FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=50000)
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/fees/{fee.id}', {
            'amount': '55000.00'
        })
        assert resp.status_code == status.HTTP_200_OK, resp.content
        fee.refresh_from_db()
        assert float(fee.amount) == 55000.00
        assert fee.course == course
        assert str(fee.id) == resp.data['id']

    def test_counselor_cannot_patch_fee(self):
        fee = FeeStructureFactory(fee_type=FeeStructure.FEE_TUITION, amount=50000)
        client = self.counselor_client()
        resp = client.patch(f'/api/v1/fees/{fee.id}', {
            'amount': '55000.00'
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unchanged_fee_type_can_be_saved(self):
        course = CourseFactory()
        fee = FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=50000)
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/fees/{fee.id}', {
            'fee_type': FeeStructure.FEE_TUITION,
            'amount': '55000.00'
        })
        assert resp.status_code == status.HTTP_200_OK

    def test_changing_to_duplicate_active_fee_type_fails(self):
        course = CourseFactory()
        fee1 = FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=50000)
        fee2 = FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_ADMISSION, amount=5000)
        client = self.super_admin_client()
        resp = client.patch(f'/api/v1/fees/{fee2.id}', {
            'fee_type': FeeStructure.FEE_TUITION
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'fee_type' in resp.data
    def test_fee_structure_amount_must_be_positive(self):
        course = CourseFactory()
        client = self.super_admin_client()

        # Create with 0 amount -> should be rejected
        resp = client.post('/api/v1/fees', {
            'course': str(course.id),
            'fee_type': FeeStructure.FEE_TUITION,
            'amount': '0.00',
            'currency': 'INR',
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'amount' in resp.data

        # Create with negative amount -> should be rejected
        resp = client.post('/api/v1/fees', {
            'course': str(course.id),
            'fee_type': FeeStructure.FEE_TUITION,
            'amount': '-1000.00',
            'currency': 'INR',
            'is_active': True,
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'amount' in resp.data

        # Patch with negative amount -> should be rejected
        fee = FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=50000)
        resp = client.patch(f'/api/v1/fees/{fee.id}', {
            'amount': '-500.00'
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'amount' in resp.data

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


@pytest.mark.django_db
class TestSubCenterUniversitiesAccess(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.subcenter_client = self._client(SystemUser.ROLE_SUBCENTER, self.center_a)
        
        # Mapped university
        self.uni_mapped = UniversityFactory(name="Mapped Uni", state="Kerala", is_active=True)
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=self.uni_mapped)
        self.course_mapped = CourseFactory(university=self.uni_mapped, name="Mapped Course", is_active=True)
        self.fee_mapped = FeeStructureFactory(course=self.course_mapped, fee_type=FeeStructure.FEE_TUITION, amount=10000)
        self.doc_mapped = UniversityDocVault.objects.create(
            university=self.uni_mapped, doc_type='prospectus', title='Mapped Prospectus',
            s3_object_uri='s3://bucket/mapped.pdf'
        )

        # Unmapped university
        self.uni_unmapped = UniversityFactory(name="Unmapped Uni", state="Karnataka", is_active=True)
        self.course_unmapped = CourseFactory(university=self.uni_unmapped, name="Unmapped Course", is_active=True)
        self.fee_unmapped = FeeStructureFactory(course=self.course_unmapped, fee_type=FeeStructure.FEE_TUITION, amount=20000)
        self.doc_unmapped = UniversityDocVault.objects.create(
            university=self.uni_unmapped, doc_type='prospectus', title='Unmapped Prospectus',
            s3_object_uri='s3://bucket/unmapped.pdf'
        )

    def test_subcenter_can_list_mapped_universities(self):
        resp = self.subcenter_client.get('/api/v1/universities')
        assert resp.status_code == status.HTTP_200_OK
        names = [u['name'] for u in resp.data['results']]
        assert "Mapped Uni" in names
        assert "Unmapped Uni" not in names

    def test_subcenter_cannot_retrieve_unmapped_university_directly(self):
        resp = self.subcenter_client.get(f'/api/v1/universities/{self.uni_unmapped.id}')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_subcenter_can_retrieve_mapped_university_directly(self):
        resp = self.subcenter_client.get(f'/api/v1/universities/{self.uni_mapped.id}')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['name'] == "Mapped Uni"

    def test_subcenter_sees_courses_only_from_mapped_universities(self):
        resp = self.subcenter_client.get('/api/v1/courses')
        assert resp.status_code == status.HTTP_200_OK
        names = [c['name'] for c in resp.data['results']]
        assert "Mapped Course" in names
        assert "Unmapped Course" not in names

    def test_subcenter_cannot_retrieve_course_belonging_to_unmapped_university_directly(self):
        resp = self.subcenter_client.get(f'/api/v1/courses/{self.course_unmapped.id}')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_subcenter_sees_fee_structures_only_for_mapped_university_courses(self):
        resp = self.subcenter_client.get('/api/v1/fees')
        assert resp.status_code == status.HTTP_200_OK
        ids = [f['id'] for f in resp.data['results']]
        assert str(self.fee_mapped.id) in ids
        assert str(self.fee_unmapped.id) not in ids

    def test_subcenter_cannot_retrieve_unmapped_fee_directly(self):
        resp = self.subcenter_client.get(f'/api/v1/fees/{self.fee_unmapped.id}')
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_subcenter_cannot_post_university(self):
        resp = self.subcenter_client.post('/api/v1/universities', {
            'name': 'New SC Uni',
            'state': 'Kerala',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_subcenter_cannot_patch_university(self):
        resp = self.subcenter_client.patch(f'/api/v1/universities/{self.uni_mapped.id}', {
            'name': 'Changed',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_subcenter_cannot_delete_university(self):
        resp = self.subcenter_client.delete(f'/api/v1/universities/{self.uni_mapped.id}')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_subcenter_cannot_post_patch_delete_course(self):
        # Create
        resp = self.subcenter_client.post('/api/v1/courses', {
            'university': str(self.uni_mapped.id),
            'name': 'New Course',
            'stream': 'Undergraduate',
            'duration_months': 36,
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Update
        resp = self.subcenter_client.patch(f'/api/v1/courses/{self.course_mapped.id}', {
            'name': 'Changed Name',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Delete
        resp = self.subcenter_client.delete(f'/api/v1/courses/{self.course_mapped.id}')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_subcenter_cannot_post_patch_delete_fee(self):
        # Create
        resp = self.subcenter_client.post('/api/v1/fees', {
            'course': str(self.course_mapped.id),
            'fee_type': FeeStructure.FEE_TUITION,
            'amount': '15000.00',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Update
        resp = self.subcenter_client.patch(f'/api/v1/fees/{self.fee_mapped.id}', {
            'amount': '12000.00',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Delete
        resp = self.subcenter_client.delete(f'/api/v1/fees/{self.fee_mapped.id}')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_subcenter_document_scoping(self):
        # List
        resp = self.subcenter_client.get('/api/v1/prospectus')
        assert resp.status_code == status.HTTP_200_OK
        titles = [d['title'] for d in resp.data['results']]
        assert 'Mapped Prospectus' in titles
        assert 'Unmapped Prospectus' not in titles

        # Retrieve direct unmapped doc
        resp = self.subcenter_client.get(f'/api/v1/prospectus/{self.doc_unmapped.id}')
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSubCenterUniversityMappingWorkflow(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.super_admin_client = self._client(SystemUser.ROLE_SUPER_ADMIN)
        self.subcenter_client = self._client(SystemUser.ROLE_SUBCENTER, self.center_a)
        self.uni_1 = UniversityFactory(name="Uni One", is_active=True)
        self.uni_2 = UniversityFactory(name="Uni Two", is_active=True)

    def test_super_admin_can_manage_mappings(self):
        # 1. List initially empty mappings
        resp = self.super_admin_client.get('/api/v1/sub-center-university-mappings')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 0

        # 2. Create mapping for self.center_a and self.uni_1
        resp = self.super_admin_client.post('/api/v1/sub-center-university-mappings', {
            'sub_center': str(self.center_a.id),
            'university': str(self.uni_1.id)
        })
        assert resp.status_code == status.HTTP_201_CREATED
        mapping_id = resp.data['id']

        # 3. Prevent duplicate mapping
        resp = self.super_admin_client.post('/api/v1/sub-center-university-mappings', {
            'sub_center': str(self.center_a.id),
            'university': str(self.uni_1.id)
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # 4. Verify center_a can now view uni_1, but not uni_2
        resp = self.subcenter_client.get('/api/v1/universities')
        assert resp.status_code == status.HTTP_200_OK
        uni_names = [u['name'] for u in resp.data['results']]
        assert "Uni One" in uni_names
        assert "Uni Two" not in uni_names

        # 5. Delete mapping
        resp = self.super_admin_client.delete(f'/api/v1/sub-center-university-mappings/{mapping_id}')
        assert resp.status_code == status.HTTP_204_NO_CONTENT

        # 6. Verify center_a can no longer view uni_1
        resp = self.subcenter_client.get('/api/v1/universities')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['count'] == 0

        # 7. Confirm deletion did not remove University or SubCenter
        assert University.objects.filter(id=self.uni_1.id).exists()
        assert SubCenter.objects.filter(id=self.center_a.id).exists()

    def test_subcenter_user_blocked_from_mapping_mutations(self):
        # Read/List mapping
        resp = self.subcenter_client.get('/api/v1/sub-center-university-mappings')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Create mapping
        resp = self.subcenter_client.post('/api/v1/sub-center-university-mappings', {
            'sub_center': str(self.center_a.id),
            'university': str(self.uni_1.id)
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestUniversityShareResolution(BaseAPITestCase):

    def test_unresolved_university_share_blocks_commission_calculation(self):
        # Create university with default_university_share_percent=0 directly
        uni = University.objects.create(
            name="Unresolved share Uni",
            state="Kerala",
            accreditation="NAAC A+",
            default_university_share_percent=0,
            is_active=True
        )
        course = CourseFactory(university=uni, university_share_percent=None)
        FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=10000)

        # 1. Block commission breakdown API
        client = self.super_admin_client()
        resp = client.get(f'/api/v1/courses/{course.id}/commission')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unable to determine the University Share" in resp.data['detail']

        # 2. Block Enrollment creation validation
        student = StudentFactory(sub_center=self.center_a)
        session = IntakeSessionFactory()
        resp = client.post('/api/v1/enrollments', {
            'student': str(student.id),
            'course': str(course.id),
            'session': str(session.id),
            'status': 'Applied'
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unable to determine the University Share" in str(resp.data)

        # 3. Block Repayment checkout API
        # Create enrollment directly via model to bypass serializer validation
        enrollment = Enrollment.objects.create(
            sub_center=self.center_a,
            student=student,
            course=course,
            session=session,
            status='Enrollment Generated'
        )
        resp = client.post(f'/api/v1/enrollments/{enrollment.id}/repayment_checkout', {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unable to determine the University Share" in resp.data['detail']

    def test_course_save_validation_with_resolved_shares(self):
        client = self.super_admin_client()

        # 1. University has a valid default share + Course Share blank -> Save succeeds
        uni_valid = University.objects.create(
            name="Valid Default Share Uni",
            state="Kerala",
            accreditation="NAAC A+",
            default_university_share_percent=50.00,
            is_active=True
        )
        resp = client.post('/api/v1/courses', {
            'name': 'Course Blank Share',
            'university': str(uni_valid.id),
            'stream': 'Undergraduate',
            'duration_months': 12,
            'university_share_percent': None
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED

        # 2. University default share missing (0) + Course Share entered -> Save succeeds
        uni_invalid = University.objects.create(
            name="Invalid Default Share Uni",
            state="Kerala",
            accreditation="NAAC A+",
            default_university_share_percent=0,
            is_active=True
        )
        resp2 = client.post('/api/v1/courses', {
            'name': 'Course Overriden Share',
            'university': str(uni_invalid.id),
            'stream': 'Undergraduate',
            'duration_months': 12,
            'university_share_percent': 40.00
        }, format='json')
        assert resp2.status_code == status.HTTP_201_CREATED

        # 3. Both missing -> Save fails with validation message
        resp3 = client.post('/api/v1/courses', {
            'name': 'Course Both Blank Share',
            'university': str(uni_invalid.id),
            'stream': 'Undergraduate',
            'duration_months': 12,
            'university_share_percent': None
        }, format='json')
        assert resp3.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unable to determine the University Share" in str(resp3.data['university_share_percent'][0])

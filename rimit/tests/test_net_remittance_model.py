from decimal import Decimal

import pytest
from rest_framework import status

from apps.aggregator.models import FeeStructure
from apps.partners.models import SubCenterUniversityMapping
from tests.base import BaseAPITestCase
from tests.factories import (
    UniversityFactory,
    CourseFactory,
    FeeStructureFactory,
    StudentFactory,
)


@pytest.mark.django_db
class TestNetRemittanceBatchCheckout(BaseAPITestCase):

    def _setup_course_with_fee(self, *, total_fee: int, uni_default_pct: Decimal, course_override_pct=None):
        uni = UniversityFactory(default_university_share_percent=uni_default_pct)
        course = CourseFactory(university=uni)
        if course_override_pct is not None:
            course.university_share_percent = course_override_pct
            course.save(update_fields=['university_share_percent'])

        # Make the course total fee exact
        # Use 2 fee rows to avoid relying on factory defaults
        FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_TUITION, amount=total_fee - 1)
        FeeStructureFactory(course=course, fee_type=FeeStructure.FEE_ADMISSION, amount=1)
        return uni, course

    def test_example1_course_level_override(self):
        # Sub-center commission: 50% of gross pool
        self.center_a.commission_percent = Decimal('50.00')
        self.center_a.save(update_fields=['commission_percent'])

        uni, course = self._setup_course_with_fee(
            total_fee=100000,
            uni_default_pct=Decimal('50.00'),
            course_override_pct=Decimal('70.00'),
        )
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)

        s1 = StudentFactory(sub_center=self.center_a)
        s2 = StudentFactory(sub_center=self.center_a)
        s1.course = course
        s2.course = course
        s1.save(update_fields=['course'])
        s2.save(update_fields=['course'])

        client = self.counselor_client(sub_center=self.center_a)
        resp = client.post('/api/v1/checkout/batch/', {'student_ids': [str(s1.id), str(s2.id)]}, format='json')
        assert resp.status_code == status.HTTP_200_OK, resp.data

        # Per student: net_payable = 85,000
        assert Decimal(resp.data['total_amount']) == Decimal('170000.00')
        assert len(resp.data.get('line_items', [])) == 2
        assert Decimal(resp.data['line_items'][0]['net_payable']) == Decimal('85000.00')
        assert Decimal(resp.data['line_items'][0]['sub_center_commission']) == Decimal('15000.00')
        assert Decimal(resp.data['line_items'][0]['university_share']) == Decimal('70000.00')
        assert Decimal(resp.data['line_items'][0]['rimit_commission']) == Decimal('15000.00')

    def test_example2_inherits_university_default(self):
        # Sub-center commission: 75% of gross pool
        self.center_a.commission_percent = Decimal('75.00')
        self.center_a.save(update_fields=['commission_percent'])

        uni, course = self._setup_course_with_fee(
            total_fee=100000,
            uni_default_pct=Decimal('50.00'),
            course_override_pct=None,
        )
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)

        s = StudentFactory(sub_center=self.center_a)
        s.course = course
        s.save(update_fields=['course'])

        client = self.finance_client(sub_center=self.center_a)
        resp = client.post('/api/v1/checkout/batch/', {'student_ids': [str(s.id)]}, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # net_payable = 62,500
        assert Decimal(resp.data['total_amount']) == Decimal('62500.00')
        li = resp.data['line_items'][0]
        assert Decimal(li['sub_center_commission']) == Decimal('37500.00')
        assert Decimal(li['rimit_commission']) == Decimal('12500.00')
        assert Decimal(li['university_share']) == Decimal('50000.00')

    def test_rejects_cross_center_batch(self):
        self.center_a.commission_percent = Decimal('50.00')
        self.center_a.save(update_fields=['commission_percent'])
        self.center_b.commission_percent = Decimal('50.00')
        self.center_b.save(update_fields=['commission_percent'])

        uni, course = self._setup_course_with_fee(
            total_fee=10000,
            uni_default_pct=Decimal('50.00'),
        )
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        SubCenterUniversityMapping.objects.create(sub_center=self.center_b, university=uni)

        s1 = StudentFactory(sub_center=self.center_a)
        s2 = StudentFactory(sub_center=self.center_b)
        s1.course = course
        s2.course = course
        s1.save(update_fields=['course'])
        s2.save(update_fields=['course'])

        client = self.super_admin_client()
        resp = client.post('/api/v1/checkout/batch/', {'student_ids': [str(s1.id), str(s2.id)]}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'same sub-center' in resp.data['error']

    def test_course_commission_breakdown_api(self):
        uni, course = self._setup_course_with_fee(
            total_fee=100000,
            uni_default_pct=Decimal('40.00'),
        )
        SubCenterUniversityMapping.objects.create(sub_center=self.center_a, university=uni)
        # Setup subcenter commission percent
        self.center_a.commission_percent = Decimal('60.00')
        self.center_a.save(update_fields=['commission_percent'])


        client = self.counselor_client(sub_center=self.center_a)
        # GET /api/v1/courses/{id}/commission
        resp = client.get(f'/api/v1/courses/{course.id}/commission')
        assert resp.status_code == status.HTTP_200_OK
        
        # Verify breakdown:
        # Total fee = 100,000
        # Uni share = 40,000 (40% of 100,000)
        # Gross Pool = 60,000
        # Sub-center commission = 36,000 (60% of 60,000)
        # RIMIT commission = 24,000 (60,000 - 36,000)
        # Net payable = 64,000 (100,000 - 36,000)
        assert Decimal(resp.data['total_course_fee']) == Decimal('100000.00')
        assert Decimal(resp.data['university_share']) == Decimal('40000.00')
        assert Decimal(resp.data['gross_commission_pool']) == Decimal('60000.00')
        assert Decimal(resp.data['sub_center_commission']) == Decimal('36000.00')
        assert Decimal(resp.data['rimit_commission']) == Decimal('24000.00')
        assert Decimal(resp.data['net_payable']) == Decimal('64000.00')


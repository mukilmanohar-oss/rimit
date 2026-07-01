"""
Test factories for the RIMIT B2B Aggregator.

Used by all test modules to create consistent test data.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from datetime import date
from apps.partners.models import SubCenter, SystemUser
from apps.aggregator.models import University, Course, FeeStructure, UniversityDocVault
from apps.rules.models import IntakeSession, RulesConfiguration
from apps.admissions.models import Student, StudentAcademicHistory, StudentDoc, Enrollment


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    is_active = True


class SubCenterFactory(DjangoModelFactory):
    class Meta:
        model = SubCenter
    center_code = factory.Sequence(lambda n: f'KL-KOC-{n:03d}')
    name = factory.Sequence(lambda n: f'Sub Center {n}')
    location = 'Kochi, Kerala'
    state = 'Kerala'
    status = SubCenter.STATUS_ACTIVE


class SystemUserFactory(DjangoModelFactory):
    class Meta:
        model = SystemUser
    user = factory.SubFactory(UserFactory)
    sub_center = factory.SubFactory(SubCenterFactory)
    role = SystemUser.ROLE_COUNSELOR
    email = factory.LazyAttribute(lambda o: o.user.email)
    phone = '+919876543210'


class UniversityFactory(DjangoModelFactory):
    class Meta:
        model = University
    name = factory.Sequence(lambda n: f'University {n}')
    state = 'Kerala'
    accreditation = 'NAAC A+'
    is_active = True


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course
    university = factory.SubFactory(UniversityFactory)
    name = factory.Sequence(lambda n: f'Course {n}')
    stream = Course.STREAM_UG
    duration_months = 36
    is_active = True


class FeeStructureFactory(DjangoModelFactory):
    class Meta:
        model = FeeStructure
    course = factory.SubFactory(CourseFactory)
    fee_type = FeeStructure.FEE_TUITION
    amount = 50000
    is_active = True


class IntakeSessionFactory(DjangoModelFactory):
    class Meta:
        model = IntakeSession
    session_name = factory.Sequence(lambda n: f'October 202{n}')
    start_date = factory.LazyFunction(lambda: date(2026, 10, 1))
    is_active = True
    is_fresh_allowed = True


class StudentFactory(DjangoModelFactory):
    class Meta:
        model = Student
    sub_center = factory.SubFactory(SubCenterFactory)
    full_name = 'Test Student'
    dob = date(2000, 1, 1)
    primary_phone = '+919876543210'
    email = factory.LazyAttribute(lambda o: f'student{o.sub_center.id}@test.com' if o.sub_center else 'student@test.com')
    aadhar_hash = factory.Sequence(lambda n: f'fakehash{n}'.ljust(64, 'x')[:64])
    address_data = {'city': 'Kochi', 'state': 'Kerala', 'pincode': '682001'}

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Bypass TenantManager — use the unfiltered all_objects manager
        obj = model_class(**kwargs)
        obj.save(using='default')  # save() doesn't use the manager's get_queryset
        return obj


class EnrollmentFactory(DjangoModelFactory):
    class Meta:
        model = Enrollment
    sub_center = factory.SubFactory(SubCenterFactory)
    student = factory.SubFactory(StudentFactory)
    course = factory.SubFactory(CourseFactory)
    session = factory.SubFactory(IntakeSessionFactory)
    status = Enrollment.STATUS_APPLIED

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(**kwargs)
        obj.save(using='default')
        return obj

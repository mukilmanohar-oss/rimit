"""
Django management command to seed demo data for the Next.js UI.

Creates:
- 1 super admin user (admin/admin123)
- 1 academic head
- 2 sub-centers with counselors
- 3 universities with courses + fees
- 2 intake sessions (July 2026 fresh-blocked, October 2026 fresh-allowed)
- Session enforcement rule: block fresh from July
- Sample students + enrollments
- A Razorpay test payment
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from datetime import date


class Command(BaseCommand):
    help = 'Seed demo data for the RIMIT UI'

    def handle(self, *args, **options):
        from apps.partners.models import SubCenter, SystemUser
        from apps.aggregator.models import University, Course, FeeStructure, UniversityDocVault
        from apps.admissions.models import Student, Enrollment
        from apps.rules.models import IntakeSession, RulesConfiguration
        from apps.finance.models import PaymentLedger
        from apps.common.models import hash_aadhar

        with transaction.atomic():
            # ─── Users ───
            admin, _ = User.objects.get_or_create(
                username='admin',
                defaults={'email': 'admin@rimit.edu', 'is_staff': True, 'is_superuser': True},
            )
            admin.set_password('admin123')
            admin.save()
            SystemUser.objects.update_or_create(
                user=admin,
                defaults={'role': 'super_admin', 'email': 'admin@rimit.edu', 'sub_center': None},
            )

            ah_user, _ = User.objects.get_or_create(
                username='academic_head', defaults={'email': 'ah@rimit.edu'},
            )
            ah_user.set_password('ah123')
            ah_user.save()

            # ─── Sub-Centers ───
            kochi, _ = SubCenter.objects.get_or_create(
                center_code='KL-KOC-001',
                defaults={
                    'name': 'Kochi Hub', 'location': 'Kochi, Kerala', 'state': 'Kerala',
                    'status': 'active', 'contact_phone': '+914841234567', 'contact_email': 'kochi@rimit.edu',
                },
            )
            mlpm, _ = SubCenter.objects.get_or_create(
                center_code='KL-MLP-001',
                defaults={
                    'name': 'Malappuram Hub', 'location': 'Malappuram, Kerala', 'state': 'Kerala',
                    'status': 'active', 'contact_phone': '+914831234567', 'contact_email': 'mlpm@rimit.edu',
                },
            )

            SystemUser.objects.update_or_create(
                user=ah_user,
                defaults={'role': 'academic_head', 'email': 'ah@rimit.edu', 'sub_center': None},
            )

            coun_user, _ = User.objects.get_or_create(
                username='counselor_kochi', defaults={'email': 'coun.kochi@rimit.edu'},
            )
            coun_user.set_password('coun123')
            coun_user.save()
            SystemUser.objects.update_or_create(
                user=coun_user,
                defaults={'role': 'counselor', 'email': 'coun.kochi@rimit.edu', 'sub_center': kochi},
            )

            fin_user, _ = User.objects.get_or_create(
                username='finance_kochi', defaults={'email': 'fin.kochi@rimit.edu'},
            )
            fin_user.set_password('fin123')
            fin_user.save()
            SystemUser.objects.update_or_create(
                user=fin_user,
                defaults={'role': 'finance', 'email': 'fin.kochi@rimit.edu', 'sub_center': kochi},
            )

            # ─── Universities ───
            mang, _ = University.objects.get_or_create(
                name='Mangalayatan University',
                defaults={
                    'state': 'Uttar Pradesh', 'accreditation': 'NAAC A',
                    'description': 'Online & ODL programs across India.',
                    'website': 'https://mangalayatan.in', 'is_active': True,
                },
            )
            bosse, _ = University.objects.get_or_create(
                name='BOSSE (Board of Open Schooling & Skill Education)',
                defaults={
                    'state': 'Sikkim', 'accreditation': 'UGC recognized',
                    'description': 'Open schooling for skill education.', 'is_active': True,
                },
            )
            calicut, _ = University.objects.get_or_create(
                name='Calicut University Distance Education',
                defaults={
                    'state': 'Kerala', 'accreditation': 'NAAC A+',
                    'description': 'Distance learning programs.', 'is_active': True,
                },
            )

            # ─── Courses + Fees ───
            courses_data = [
                (mang, 'BCA Online', 'Undergraduate', 36, 45000),
                (mang, 'MBA Online', 'Postgraduate', 24, 120000),
                (mang, 'B.Com Online', 'Undergraduate', 36, 38000),
                (bosse, '10th Secondary', 'Open Schooling', 12, 8500),
                (bosse, '12th Senior Secondary', 'Open Schooling', 12, 9500),
                (calicut, 'BA English', 'Undergraduate', 36, 25000),
                (calicut, 'MA History', 'Postgraduate', 24, 32000),
                (calicut, 'Diploma in Computer Applications', 'Diploma', 6, 12000),
            ]
            course_objs = []
            for uni, name, stream, dur, tuition in courses_data:
                c, _ = Course.objects.get_or_create(
                    university=uni, name=name,
                    defaults={
                        'stream': stream, 'duration_months': dur,
                        'eligibility_text': '10+2 or equivalent' if stream != 'Open Schooling' else '8th pass',
                        'is_active': True,
                    },
                )
                course_objs.append(c)
                FeeStructure.objects.get_or_create(
                    course=c, fee_type='tuition', defaults={'amount': tuition, 'is_active': True},
                )
                FeeStructure.objects.get_or_create(
                    course=c, fee_type='admission', defaults={'amount': min(2000, tuition // 20), 'is_active': True},
                )

            # ─── Prospectus docs ───
            UniversityDocVault.objects.get_or_create(
                university=mang, title='Mangalayatan 2026 Prospectus',
                defaults={
                    'doc_type': 'prospectus', 's3_object_uri': 's3://rimit-docs/mang-prospectus-2026.pdf',
                    'mime_type': 'application/pdf', 'is_public': True,
                },
            )
            UniversityDocVault.objects.get_or_create(
                university=bosse, title='BOSSE Academic Calendar 2026',
                defaults={
                    'doc_type': 'calendar', 's3_object_uri': 's3://rimit-docs/bosse-cal-2026.pdf',
                    'mime_type': 'application/pdf', 'is_public': True,
                },
            )

            # ─── Intake Sessions ───
            july, _ = IntakeSession.objects.get_or_create(
                session_name='July 2026',
                defaults={
                    'start_date': date(2026, 7, 1), 'end_date': date(2026, 7, 31),
                    'is_active': True, 'is_fresh_allowed': False,
                },
            )
            october, _ = IntakeSession.objects.get_or_create(
                session_name='October 2026',
                defaults={
                    'start_date': date(2026, 10, 1), 'end_date': date(2026, 10, 31),
                    'is_active': True, 'is_fresh_allowed': True,
                },
            )

            # ─── Session Enforcement Matrix Rule ───
            RulesConfiguration.objects.update_or_create(
                rule_name='block_fresh_july',
                defaults={
                    'description': 'Fresh candidates cannot enroll in July session; route to October.',
                    'conditions': {
                        'student_is_fresh': True,
                        'session_name_in': ['July 2026'],
                        'action': 'reject',
                        'suggested_session': 'October 2026',
                        'reason': 'Fresh candidates must start in October intake. July is for continuing students only.',
                    },
                    'is_active': True, 'priority': 10,
                },
            )

            # ─── Sample students + enrollments (Kochi) ───
            students_data = [
                ('Rahul Sharma', '1998-05-12', 'M', '+919876543210', 'rahul@example.com', '123456789012'),
                ('Priya Nair', '2000-08-23', 'F', '+919876543211', 'priya@example.com', '234567890123'),
                ('Arun Kumar', '1995-12-01', 'M', '+919876543212', 'arun@example.com', '345678901234'),
                ('Sneha Pillai', '1999-03-15', 'F', '+919876543213', 'sneha@example.com', '456789012345'),
            ]
            for i, (name, dob, gender, phone, email, aadhar) in enumerate(students_data):
                s, _ = Student.all_objects.get_or_create(
                    aadhar_hash=hash_aadhar(aadhar),
                    defaults={
                        'sub_center': kochi, 'full_name': name, 'dob': dob,
                        'gender': gender, 'primary_phone': phone, 'email': email, 'is_active': True,
                    },
                )
                if i < 2:
                    course = course_objs[i * 2]
                    status = ['Enrolled', 'Fee Paid'][i]
                    Enrollment.all_objects.get_or_create(
                        student=s, course=course, session=october,
                        defaults={'sub_center': kochi, 'status': status},
                    )
                elif i == 2:
                    Enrollment.all_objects.get_or_create(
                        student=s, course=course_objs[3], session=october,
                        defaults={'sub_center': kochi, 'status': 'Applied'},
                    )

            # ─── Sample payment ───
            try:
                arun = Student.all_objects.get(email='arun@example.com')
                arun_enroll = Enrollment.all_objects.filter(student=arun).first()
                if arun_enroll and arun_enroll.status != 'Fee Paid':
                    PaymentLedger.all_objects.get_or_create(
                        transaction_ref='pay_demo_001',
                        defaults={
                            'enrollment': arun_enroll, 'sub_center': kochi,
                            'amount_paid': 8500.00, 'status': 'captured', 'gateway': 'razorpay',
                        },
                    )
                    arun_enroll.status = 'Fee Paid'
                    arun_enroll.save()
            except Exception:
                pass

            self.stdout.write(self.style.SUCCESS(
                '✓ Demo data seeded.\n\n'
                'Login credentials:\n'
                '  Super Admin:    admin / admin123\n'
                '  Academic Head:  academic_head / ah123\n'
                '  Counselor:      counselor_kochi / coun123\n'
                '  Finance:        finance_kochi / fin123\n'
            ))

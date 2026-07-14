
import zipfile
import io
from celery import shared_task
from apps.admissions.models import Student, StudentDoc
from django.core.files.base import ContentFile

@shared_task
def generate_student_documents_zip(student_id, admin_email):
    try:
        student = Student.objects.get(id=student_id)
        docs = StudentDoc.objects.filter(student=student)
        
        if not docs.exists():
            return "No documents found"
            
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for doc in docs:
                if doc.file:
                    file_name = os.path.basename(doc.file.name)
                    zip_file.writestr(file_name, doc.file.read())
                    
        # Normally you would upload zip_buffer to S3/MinIO and send email
        # For now, simulate success
        print(f"Generated ZIP with {docs.count()} files for {student.full_name}. Emailing link to {admin_email}.")
        
        return True
    except Exception as e:
        print(f"Error generating zip: {e}")
        return False

import os
import uuid
import boto3
from urllib.parse import urljoin
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def handle_file_upload(file_obj, directory, filename_prefix=""):
    """
    Uploads a file object to local storage or S3 based on settings.
    Returns the URI of the uploaded file.
    """
    ext = os.path.splitext(file_obj.name)[1]
    unique_name = f"{filename_prefix}{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(directory, unique_name).replace('\\', '/')
    
    if getattr(settings, 'USE_LOCAL_STORAGE', True):
        # Ensure LOCAL_STORAGE_PATH exists
        path = getattr(settings, 'LOCAL_STORAGE_PATH', settings.MEDIA_ROOT)
        os.makedirs(path, exist_ok=True)
        
        fs = FileSystemStorage(location=path)
        saved_name = fs.save(file_path, file_obj)
        
        # We store the relative path or media url as the URI
        # For simplicity, just return the media url
        return fs.url(saved_name)
    else:
        # S3 / MinIO
        endpoint = settings.AWS_S3_ENDPOINT_URL
        if isinstance(endpoint, str):
            endpoint = endpoint.strip(' "\'')
            if not endpoint:
                endpoint = None

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=endpoint,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Read file contents
        file_obj.seek(0)
        s3.upload_fileobj(
            file_obj,
            settings.AWS_STORAGE_BUCKET_NAME,
            file_path,
            ExtraArgs={'ContentType': getattr(file_obj, 'content_type', 'application/octet-stream')}
        )
        
        # Return standard s3 uri format or direct url
        if endpoint:
            return urljoin(endpoint, f"{settings.AWS_STORAGE_BUCKET_NAME}/{file_path}")
        else:
            return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_path}"

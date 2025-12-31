"""
Validation utilities
"""
import re
from werkzeug.utils import secure_filename
import os


ALLOWED_DATASET_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls', 'parquet', 'tsv'}
ALLOWED_MODEL_EXTENSIONS = {'pkl', 'joblib', 'h5', 'onnx', 'pt', 'pth', 'pb'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, None


def allowed_file(filename, file_type='dataset'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'dataset':
        return ext in ALLOWED_DATASET_EXTENSIONS
    elif file_type == 'model':
        return ext in ALLOWED_MODEL_EXTENSIONS
    elif file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    
    return False


def secure_filename_custom(filename):
    """Create secure filename"""
    return secure_filename(filename)


def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def get_file_format(filename):
    """Get file format from filename"""
    if '.' not in filename:
        return None
    return filename.rsplit('.', 1)[1].lower()

# Flask server Configuration
DEBUG = False
SQLALCHEMY_ECHO = False
SECRET_KEY = "REPLACE BY SOMETHING SECURE"
SQLALCHEMY_DATABASE_URI = "sqlite:///:memory"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Files configuration
FILESTORE_DIR = "filestore"  # folder name on disk
FILESTORE_PATH = "/file"   # URL path prefix
MAX_UPLOAD_SIZE = 32 * 1024 * 1024  # 32MB
INITIAL_YEAR = 2010  # year for which files are stored
FILE_ICONS = {"audio/": "file-audio", "video/": "file-video", "image/": "file-image", "text/": "file-alt",
			"application/pdf": "file-pdf", "application/msword": "file-word",  "application/mspowerpoint": "file-powerpoint",
			"application/excel": "file-excel", "application/zip": "file-archive", "default": "file"}

# Folder structure configuration
SUBJECT_SUBFOLDERS = ['exams', 'homework', 'literature', 'misc', 'summaries']

# Crowd REST configuration
CROWD_API_URL = "http://my.cs-students.nl:8095/crowd/"
CROWD_API_USER = ""
CROWD_API_PASS = ""
CROWD_API_ADMIN_GROUP = "Admin"  # The name of the administrators group in crowd

import os
from django.core.exceptions import ValidationError

ALLOWED_VIDEO_EXTENSIONS = ["mp4", "webm", "mov", "mkv"]
ALLOWED_CONTENT_TYPES = ["video/mp4", "video/webm", "video/quicktime", "video/x-matroska"]
MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150 MB (adjust as needed)

def validate_video_file(file):
    # check size
    if file.size > MAX_VIDEO_SIZE:
        raise ValidationError(f"File too large. Max size is {MAX_VIDEO_SIZE // (1024*1024)} MB")

    # check extension
    name = str(file.name)
    ext = name.split(".")[1] if "." in name else ""
    if ext.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError("Unsupported file extension.")

    # optional: check content_type if file has content_type attribute (DRF file)
    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("Unsupported content type.")

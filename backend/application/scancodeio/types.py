from dataclasses import dataclass, field
from typing import Optional

from django.core.files.uploadedfile import UploadedFile

# Limit of Project.name in ScanCode.io v38.2.0
SCANCODEIO_PROJECT_NAME_MAX_LENGTH = 100


@dataclass
class CreateProjectParameters:
    name: str
    pipeline: str
    input_urls: list[str] = field(default_factory=list)
    upload_file: Optional[UploadedFile] = None
    execute_now: bool = False

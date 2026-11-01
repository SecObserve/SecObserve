from dataclasses import dataclass, field
from typing import Optional

from django.core.files.uploadedfile import UploadedFile


@dataclass
class CreateProjectParameters:
    name: str
    pipeline: str
    input_urls: list[str] = field(default_factory=list)
    upload_file: Optional[UploadedFile] = None
    execute_now: bool = False

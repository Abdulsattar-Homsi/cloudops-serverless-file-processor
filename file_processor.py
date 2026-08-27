import csv
import hashlib
import io
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".txt", ".csv"}


class ProcessingValidationError(Exception):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


def process_file(blob_name: str, content: bytes) -> dict[str, Any]:
    extension = PurePosixPath(blob_name).suffix.lower()

    _validate_file(extension, content)

    try:
        decoded_content = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ProcessingValidationError(
            error_code="INVALID_ENCODING",
            message="The file must use UTF-8 encoding.",
        ) from error

    common_report = {
        "status": "processed",
        "source_blob": blob_name,
        "file_type": extension.removeprefix("."),
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    if extension == ".txt":
        metrics = _process_text(decoded_content)
    else:
        metrics = _process_csv(decoded_content)

    return {
        **common_report,
        "metrics": metrics,
    }


def build_failure_report(
    blob_name: str,
    error: ProcessingValidationError,
) -> dict[str, Any]:
    return {
        "status": "failed",
        "source_blob": blob_name,
        "error_code": error.error_code,
        "error_message": error.message,
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _validate_file(extension: str, content: bytes) -> None:
    if extension not in SUPPORTED_EXTENSIONS:
        raise ProcessingValidationError(
            error_code="UNSUPPORTED_FILE_TYPE",
            message="Only .txt and .csv files are supported.",
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ProcessingValidationError(
            error_code="FILE_TOO_LARGE",
            message="The file exceeds the 10 MiB size limit.",
        )


def _process_text(content: str) -> dict[str, Any]:
    return {
        "line_count": len(content.splitlines()),
        "word_count": len(content.split()),
        "character_count": len(content),
    }


def _process_csv(content: str) -> dict[str, Any]:
    try:
        rows = list(csv.reader(io.StringIO(content)))
    except csv.Error as error:
        raise ProcessingValidationError(
            error_code="INVALID_CSV",
            message="The CSV file could not be parsed.",
        ) from error

    if not rows:
        return {
            "row_count": 0,
            "column_count": 0,
            "headers": [],
        }

    headers = rows[0]
    data_rows = rows[1:]

    if any(len(row) != len(headers) for row in data_rows):
        raise ProcessingValidationError(
            error_code="INVALID_CSV_STRUCTURE",
            message="All CSV rows must contain the same number of columns.",
        )

    return {
        "row_count": len(data_rows),
        "column_count": len(headers),
        "headers": headers,
    }
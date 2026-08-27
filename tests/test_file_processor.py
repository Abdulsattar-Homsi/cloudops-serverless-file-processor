import pytest

from file_processor import (
    MAX_FILE_SIZE_BYTES,
    ProcessingValidationError,
    build_failure_report,
    process_file,
)


def test_process_text_file() -> None:
    content = b"Hello Azure\nCloudOps processing"

    report = process_file("incoming/example.txt", content)

    assert report["status"] == "processed"
    assert report["file_type"] == "txt"
    assert report["size_bytes"] == len(content)
    assert report["metrics"]["line_count"] == 2
    assert report["metrics"]["word_count"] == 4
    assert report["metrics"]["character_count"] == len(content)
    assert len(report["sha256"]) == 64


def test_process_csv_file() -> None:
    content = b"id,name,status\n1,Task One,open\n2,Task Two,closed\n"

    report = process_file("incoming/tasks.csv", content)

    assert report["status"] == "processed"
    assert report["file_type"] == "csv"
    assert report["metrics"]["row_count"] == 2
    assert report["metrics"]["column_count"] == 3
    assert report["metrics"]["headers"] == ["id", "name", "status"]


def test_reject_unsupported_file_type() -> None:
    with pytest.raises(ProcessingValidationError) as exception:
        process_file("incoming/image.jpg", b"fake image content")

    assert exception.value.error_code == "UNSUPPORTED_FILE_TYPE"


def test_reject_invalid_utf8() -> None:
    with pytest.raises(ProcessingValidationError) as exception:
        process_file("incoming/invalid.txt", b"\xff\xfe")

    assert exception.value.error_code == "INVALID_ENCODING"


def test_reject_oversized_file() -> None:
    oversized_content = b"x" * (MAX_FILE_SIZE_BYTES + 1)

    with pytest.raises(ProcessingValidationError) as exception:
        process_file("incoming/large.txt", oversized_content)

    assert exception.value.error_code == "FILE_TOO_LARGE"


def test_reject_inconsistent_csv_rows() -> None:
    content = b"id,name\n1,Alice\n2,Bob,unexpected\n"

    with pytest.raises(ProcessingValidationError) as exception:
        process_file("incoming/invalid.csv", content)

    assert exception.value.error_code == "INVALID_CSV_STRUCTURE"


def test_build_failure_report() -> None:
    error = ProcessingValidationError(
        error_code="TEST_ERROR",
        message="Test validation error.",
    )

    report = build_failure_report("incoming/test.txt", error)

    assert report["status"] == "failed"
    assert report["source_blob"] == "incoming/test.txt"
    assert report["error_code"] == "TEST_ERROR"
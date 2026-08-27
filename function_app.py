import logging

import azure.functions as func

from file_processor import (
    ProcessingValidationError,
    build_failure_report,
    process_file,
)


app = func.FunctionApp()


@app.function_name(name="process_blob_upload")
@app.blob_trigger(
    arg_name="input_blob",
    path="incoming/{name}",
    connection="CloudOpsStorage",
    source=func.BlobSource.EVENT_GRID,
)
def process_blob_upload(input_blob: func.InputStream) -> None:
    blob_name = input_blob.name
    content = input_blob.read()

    logging.info(
        "CloudOps processing started: source_blob=%s size_bytes=%s",
        blob_name,
        input_blob.length,
    )

    try:
        report = process_file(blob_name, content)

        logging.info(
            "CloudOps processing completed: source_blob=%s status=%s sha256=%s",
            blob_name,
            report["status"],
            report["sha256"],
        )

    except ProcessingValidationError as error:
        failure_report = build_failure_report(blob_name, error)

        logging.warning(
            "CloudOps validation failed: source_blob=%s error_code=%s",
            blob_name,
            failure_report["error_code"],
        )
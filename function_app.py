import json
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
@app.blob_output(
    arg_name="processed_output",
    path="processed/{name}.json",
    connection="CloudOpsStorage",
)
@app.blob_output(
    arg_name="failed_output",
    path="failed/{name}.json",
    connection="CloudOpsStorage",
)
def process_blob_upload(
    input_blob: func.InputStream,
    processed_output: func.Out[str],
    failed_output: func.Out[str],
) -> None:
    blob_name = input_blob.name
    content = input_blob.read()

    logging.info(
        "CloudOps processing started: source_blob=%s size_bytes=%s",
        blob_name,
        input_blob.length,
    )

    try:
        report = process_file(blob_name, content)

        processed_output.set(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            )
        )

        logging.info(
            "CloudOps processing completed: source_blob=%s status=%s sha256=%s",
            blob_name,
            report["status"],
            report["sha256"],
        )

    except ProcessingValidationError as error:
        failure_report = build_failure_report(blob_name, error)

        failed_output.set(
            json.dumps(
                failure_report,
                indent=2,
                ensure_ascii=False,
            )
        )

        logging.warning(
            "CloudOps validation failed: source_blob=%s error_code=%s",
            blob_name,
            failure_report["error_code"],
        )
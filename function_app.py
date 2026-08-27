import logging

import azure.functions as func


app = func.FunctionApp()


@app.function_name(name="process_blob_upload")
@app.blob_trigger(
    arg_name="input_blob",
    path="incoming/{name}",
    connection="CloudOpsStorage",
    source=func.BlobSource.EVENT_GRID,
)
def process_blob_upload(input_blob: func.InputStream) -> None:
    logging.info(
        "CloudOps received blob: name=%s size_bytes=%s",
        input_blob.name,
        input_blob.length,
    )
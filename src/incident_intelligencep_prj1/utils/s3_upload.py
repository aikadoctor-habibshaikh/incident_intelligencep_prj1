from pathlib import Path
import logging
import boto3

logger = logging.getLogger(__name__)


class S3Uploader:

    def __init__(self, region=None):
        self.s3 = boto3.client("s3", region_name=region)

    def upload_folder(
        self,
        bucket_name: str,
        prefix: str,
        local_folder: str,
    ):

        local_path = Path(local_folder)

        if not local_path.exists():
            logger.warning("%s does not exist.", local_folder)
            return

        for file in local_path.rglob("*"):

            if file.is_dir():
                continue

            relative = file.relative_to(local_path)

            s3_key = f"{prefix}{relative}"

            logger.info("Uploading %s", s3_key)

            self.s3.upload_file(
                str(file),
                bucket_name,
                s3_key
            )

        logger.info("Reports uploaded successfully.")
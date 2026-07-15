from pathlib import Path
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Downloader:

    def __init__(self, region=None):
        self.s3 = boto3.client("s3", region_name=region)

    def download_folder(
        self,
        bucket_name: str,
        prefix: str,
        local_dir: str,
    ) -> None:

        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        paginator = self.s3.get_paginator("list_objects_v2")

        for page in paginator.paginate(
            Bucket=bucket_name,
            Prefix=prefix
        ):

            if "Contents" not in page:
                logger.warning("No files found in %s/%s", bucket_name, prefix)
                return

            for obj in page["Contents"]:

                key = obj["Key"]

                if key.endswith("/"):
                    continue

                filename = Path(key).name

                destination = local_path / filename

                logger.info("Downloading %s", key)

                self.s3.download_file(
                    bucket_name,
                    key,
                    str(destination)
                )

        logger.info("Input files downloaded successfully.")
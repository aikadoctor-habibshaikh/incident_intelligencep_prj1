import os
from pathlib import Path
from typing import Optional, Sequence

import boto3
from botocore.exceptions import ClientError


def get_s3_client(region_name: Optional[str] = None):
    """Create an S3 client using env vars or the AWS shared config chain."""
    session_kwargs = {}
    if region_name or os.getenv("AWS_REGION"):
        session_kwargs["region_name"] = region_name or os.getenv("AWS_REGION")

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    if aws_access_key_id and aws_secret_access_key:
        session_kwargs.update(
            {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "aws_session_token": aws_session_token,
            }
        )

    return boto3.client("s3", **session_kwargs)


def get_s3_config() -> tuple[str, str, str]:
    bucket = os.getenv("S3_BUCKET", "").strip()
    input_prefix = os.getenv("S3_INPUT_PREFIX", "input/dynatrace_logs/").strip().strip("/")
    output_prefix = os.getenv("S3_OUTPUT_PREFIX", "output").strip().strip("/")
    if not input_prefix:
        input_prefix = "input/dynatrace_logs"
    if not output_prefix:
        output_prefix = "output"
    return bucket, input_prefix, output_prefix


def is_s3_enabled() -> bool:
    bucket, _, _ = get_s3_config()
    return bool(bucket)


def download_inputs_from_s3(
    client=None,
    bucket: Optional[str] = None,
    prefix: str = "input/dynatrace_logs",
    destination_dir: Optional[Path] = None,
) -> list[str]:
    """Download objects from S3 into a local directory."""
    bucket_name = bucket or get_s3_config()[0]
    if not bucket_name:
        return []

    destination = destination_dir or Path("input") / "dynatrace_logs"
    destination.mkdir(parents=True, exist_ok=True)

    s3_client = client or get_s3_client()
    prefix_value = prefix.strip("/")
    if prefix_value:
        prefix_value = f"{prefix_value}/"

    downloaded_objects: list[str] = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix_value):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            relative_key = key[len(prefix_value):] if key.startswith(prefix_value) else key
            file_path = destination / Path(relative_key)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            file_path.write_bytes(response["Body"].read())
            downloaded_objects.append(key)

    return downloaded_objects


def upload_outputs_to_s3(
    client=None,
    bucket: Optional[str] = None,
    prefix: str = "output",
    output_dir: Optional[Path] = None,
) -> list[str]:
    """Upload files from the local output directory to S3."""
    bucket_name = bucket or get_s3_config()[0]
    if not bucket_name:
        return []

    output_path = output_dir or Path("output")
    if not output_path.exists():
        return []

    s3_client = client or get_s3_client()
    prefix_value = prefix.strip("/")
    if not prefix_value:
        prefix_value = "output"

    uploaded_objects: list[str] = []
    for file_path in sorted(output_path.rglob("*")):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(output_path).as_posix()
        key = f"{prefix_value}/{relative_path}" if prefix_value else relative_path
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=file_path.read_bytes())
        uploaded_objects.append(key)

    return uploaded_objects

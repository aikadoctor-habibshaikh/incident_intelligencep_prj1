from pathlib import Path

from incident_intelligencep_prj1.s3_storage import download_inputs_from_s3, upload_outputs_to_s3


class FakeS3Client:
    def __init__(self, objects):
        self.objects = objects
        self.download_calls = []
        self.upload_calls = []

    def list_objects_v2(self, Bucket, Prefix):
        return {"Contents": [{"Key": key} for key in self.objects if key.startswith(Prefix)]}

    def get_object(self, Bucket, Key):
        self.download_calls.append((Bucket, Key))
        return {"Body": type("Body", (), {"read": lambda self: f"content::{Key}".encode("utf-8")})()}

    def put_object(self, Bucket, Key, Body):
        self.upload_calls.append((Bucket, Key, Body))


def test_download_inputs_from_s3_populates_local_folder(tmp_path):
    client = FakeS3Client(["input/dynatrace_logs/sample_incident_logs.jsonl"])

    output_dir = tmp_path / "input" / "dynatrace_logs"
    output_dir.mkdir(parents=True, exist_ok=True)

    download_inputs_from_s3(client=client, bucket="demo-bucket", prefix="input/", destination_dir=output_dir)

    copied_file = output_dir / "sample_incident_logs.jsonl"
    assert copied_file.exists()
    assert copied_file.read_text(encoding="utf-8") == "content::input/dynatrace_logs/sample_incident_logs.jsonl"


def test_upload_outputs_to_s3_uploads_output_files(tmp_path):
    client = FakeS3Client([])
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "log_analysis.json").write_text("{}", encoding="utf-8")

    upload_outputs_to_s3(client=client, bucket="demo-bucket", prefix="output/", output_dir=output_dir)

    assert any(call[0] == "demo-bucket" and call[1] == "output/log_analysis.json" for call in client.upload_calls)

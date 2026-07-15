import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

INPUT_BUCKET = os.getenv(
    "INPUT_BUCKET",
    "incident-intelligence-input"
)

OUTPUT_BUCKET = os.getenv(
    "OUTPUT_BUCKET",
    "incident-intelligence-output"
)

INPUT_PREFIX = os.getenv(
    "INPUT_PREFIX",
    "input/dynatrace_logs/"
)

OUTPUT_PREFIX = os.getenv(
    "OUTPUT_PREFIX",
    "output/"
)

LOCAL_INPUT_DIR = "input/dynatrace_logs"
LOCAL_OUTPUT_DIR = "output"
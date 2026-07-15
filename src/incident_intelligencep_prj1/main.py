#!/usr/bin/env python
import argparse
import json
import os
import sys
import warnings
from pathlib import Path

from datetime import datetime
from incident_intelligencep_prj1.config import (
    INPUT_BUCKET,
    OUTPUT_BUCKET,
    INPUT_PREFIX,
    OUTPUT_PREFIX,
    LOCAL_INPUT_DIR,
    LOCAL_OUTPUT_DIR,
    AWS_REGION,
)

from incident_intelligencep_prj1.utils.s3_download import S3Downloader
from incident_intelligencep_prj1.utils.s3_upload import S3Uploader
from incident_intelligencep_prj1.crew import IncidentIntelligencePrj1
from incident_intelligencep_prj1.fallback_analysis import analyze_logs_with_fallback, build_root_cause_report

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run(task_name: str | None = None):
    """
    Run the crew.
    """
    task_name = (task_name or os.getenv('TASK_NAME', 'full')).strip().lower()
    if task_name in {'log_analysis', 'log-analysis', 'log'}:
        selected_task = 'log_analysis'
    elif task_name in {'root_cause', 'root-cause', 'rootcause', 'remediation'}:
        selected_task = 'root_cause'
    else:
        selected_task = None

    # ensure input/output folders exist
    input_dir = Path('input') / 'dynatrace_logs'
    output_dir = Path('output')
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
    model = os.getenv('MODEL', 'gpt-4o-mini')
    api_base = os.getenv('OPENAI_API_BASE')
    if not api_key:
        print('No OpenAI API key detected. Running local fallback analysis from input logs.')
        log_analysis = analyze_logs_with_fallback(input_dir, output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'log_analysis.json').write_text(json.dumps(log_analysis, indent=2), encoding='utf-8')
        root_cause = build_root_cause_report(log_analysis)
        (output_dir / 'root_cause_analysis.json').write_text(json.dumps(root_cause, indent=2), encoding='utf-8')
        return log_analysis, root_cause

    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year),
        'log_input_path': str(input_dir),
        'output_path': str(output_dir),
        'model': model,
        'api_base': api_base,
    }

    try:
        IncidentIntelligencePrj1().build_crew(selected_task).kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        IncidentIntelligencePrj1().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        IncidentIntelligencePrj1().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    try:
        IncidentIntelligencePrj1().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def is_server_enabled() -> bool:
    """
    Returns True when the application should start the API server.

    Environment variable:
        SERVE=1 | true | yes | on
    """
    value = os.getenv("SERVE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the incident intelligence crew')
    parser.add_argument('--task', choices=['full', 'log_analysis', 'root_cause'], default=os.getenv('TASK_NAME', 'full'))
    args = parser.parse_args()
    print("=" * 80)
    print("Downloading input files from Amazon S3...")
    print("=" * 80)

    downloader = S3Downloader(AWS_REGION)

    downloader.download_folder(
        bucket_name=INPUT_BUCKET,
        prefix=INPUT_PREFIX,
        local_dir=LOCAL_INPUT_DIR,
    )
    
    run(args.task)
    
    print("=" * 80)
    print("Uploading reports to Amazon S3...")
    print("=" * 80)

    uploader = S3Uploader(AWS_REGION)

    uploader.upload_folder(
        bucket_name=OUTPUT_BUCKET,
        prefix=OUTPUT_PREFIX,
        local_folder=LOCAL_OUTPUT_DIR,
    )

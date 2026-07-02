import os
import sys
import warnings

from datetime import datetime

from log_analyst.crew import LogAnalyst

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


os.makedirs('output', exist_ok=True)

assignment = 'read log files to find out errors and present them in text format'


def run():
    """
    Run the crew.
    """
    LOG_FILE_PATH = "F:\Hadoop_2k.log_templates.csv"

    inputs = {
        'assignment': assignment,
        'log_file_path': LOG_FILE_PATH
    }

    result = LogAnalyst().crew().kickoff(inputs=inputs)
    print(result.raw)




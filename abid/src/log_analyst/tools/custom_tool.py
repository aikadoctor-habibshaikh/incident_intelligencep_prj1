from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd

class MyLogAnalystToolInput(BaseModel):
    """Input schema for MyLogAnalystTool."""
    log_file_path: str = Field(..., description="F:\Hadoop_2k.log_templates.csv")

class MyLogAnalystTool(BaseTool):
    name: str = "LogAnalysisTool"
    description: str = (
        "Analyzes a log file for errors and patterns, returning a text summary."
    )
    args_schema: Type[BaseModel] = MyLogAnalystToolInput

    def _run(self, log_file_path: str) -> str:
        try:
            # Load the log file
            df = pd.read_csv("F:\Hadoop_2k.log_templates.csv", on_bad_lines="skip", engine="python")

            # Convert to text if needed
            text_data = df.to_string()

            # Count occurrences of 'ERROR'
            error_count = text_data.upper().count("ERROR")

            # Extract sample error lines (first 5)
            error_lines = [
                line for line in text_data.split("\n") if "ERROR" in line.upper()
            ][:5]

            # Build summary
            summary = f"Total errors found: {error_count}\n"
            if error_lines:
                summary += "Sample error lines:\n" + "\n".join(error_lines)
            else:
                summary += "No error lines detected."

            return summary

        except Exception as e:
            return f"Failed to analyze logs: {e}" 


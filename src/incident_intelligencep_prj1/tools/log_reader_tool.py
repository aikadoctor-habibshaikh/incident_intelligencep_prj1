import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class LogReaderInput(BaseModel):
    log_folder: str = Field(..., description="Path to folder containing Dynatrace log files")
    service_filter: str = Field(default="", description="Optional service name filter")
    max_entries: int = Field(default=200, description="Maximum log entries to return")


class LogReaderTool(BaseTool):
    name: str = "dynatrace_log_reader"
    description: str = (
        "Reads Dynatrace JSONL or CSV logs from a local folder, summarizes error patterns, "
        "trace correlations, and anomaly clusters for incident investigation."
    )
    args_schema: Type[BaseModel] = LogReaderInput

    def _run(self, log_folder: str, service_filter: str = "", max_entries: int = 200) -> str:
        folder = Path(log_folder)
        if not folder.exists():
            return json.dumps({"error": f"Log folder not found: {log_folder}"})

        entries = []
        for file_path in sorted(folder.glob("*")):
            if file_path.suffix.lower() not in {".jsonl", ".ndjson", ".json", ".csv"}:
                continue
            entries.extend(self._read_file(file_path))

        if service_filter:
            entries = [entry for entry in entries if entry.get("service") == service_filter]

        entries = entries[:max_entries]
        if not entries:
            return json.dumps({"error": "No log entries found", "folder": str(folder)})

        error_entries = [entry for entry in entries if entry.get("logLevel") in {"ERROR", "WARN"}]
        services = sorted({entry.get("service", "unknown") for entry in entries})
        error_codes = Counter(entry.get("errorCode", "") for entry in error_entries if entry.get("errorCode"))
        trace_groups = defaultdict(list)

        for entry in entries:
            trace_id = entry.get("traceId")
            if trace_id:
                trace_groups[trace_id].append(entry)

        high_anomaly = [
            entry for entry in entries
            if float(entry.get("anomalyScore", 0) or 0) >= 0.7
        ]

        result = {
            "source": "dynatrace_log_reader",
            "folder": str(folder),
            "total_entries": len(entries),
            "error_and_warn_count": len(error_entries),
            "affected_services": services,
            "top_error_codes": [
                {"code": code, "count": count}
                for code, count in error_codes.most_common(10)
            ],
            "high_anomaly_events": high_anomaly[:15],
            "trace_correlation": [
                {
                    "trace_id": trace_id,
                    "event_count": len(group),
                    "services": sorted({item.get("service", "") for item in group}),
                    "first_seen": group[0].get("timestamp"),
                    "last_seen": group[-1].get("timestamp"),
                }
                for trace_id, group in list(trace_groups.items())[:20]
            ],
            "sample_entries": error_entries[:20],
        }
        return json.dumps(result, indent=2, default=str)

    def _read_file(self, file_path: Path):
        rows = []
        if file_path.suffix.lower() == ".csv":
            return rows

        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

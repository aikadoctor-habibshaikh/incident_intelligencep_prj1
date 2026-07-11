import json
import os
from datetime import datetime, timedelta
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class DynatraceMetricsInput(BaseModel):
    service_name: str = Field(..., description="Service name to inspect")
    time_range_minutes: int = Field(default=60, description="Lookback window in minutes")


class DynatraceMetricsTool(BaseTool):
    name: str = "dynatrace_metrics"
    description: str = (
        "Fetches Dynatrace infrastructure metrics such as CPU, memory, latency, "
        "error rate, and throughput for a service."
    )
    args_schema: Type[BaseModel] = DynatraceMetricsInput

    def _run(self, service_name: str, time_range_minutes: int = 60) -> str:
        use_mock = os.getenv("USE_MOCK_INTEGRATIONS", "true").lower() == "true"
        if not use_mock:
            live = self._fetch_live(service_name, time_range_minutes)
            if live:
                return live
        return self._build_snapshot(service_name, time_range_minutes)

    def _build_snapshot(self, service_name: str, time_range_minutes: int) -> str:
        now = datetime.utcnow()
        payload = {
            "source": "dynatrace_metrics",
            "service": service_name,
            "time_range_minutes": time_range_minutes,
            "timestamp": now.isoformat(),
            "metrics": {
                "cpu_usage_percent": 91.8,
                "memory_usage_percent": 86.4,
                "response_time_ms_p99": 4380,
                "error_rate_percent": 17.9,
                "throughput_rpm": 1185,
                "disk_io_utilization": 76.2,
                "network_latency_ms": 138,
                "db_connection_pool_usage": 94.6,
            },
            "anomalies": [
                "CPU climbed above 90 percent during the incident window",
                "Error rate moved from under 1 percent to nearly 18 percent",
                "Database connection pool usage stayed above 94 percent",
            ],
            "status": "CRITICAL",
        }
        return json.dumps(payload, indent=2)

    def _fetch_live(self, service_name: str, time_range_minutes: int):
        import httpx

        api_url = os.getenv("DYNATRACE_API_URL", "")
        api_token = os.getenv("DYNATRACE_API_TOKEN", "")
        if not api_url or not api_token:
            return None

        headers = {"Authorization": f"Api-Token {api_token}"}
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"{api_url}/api/v2/metrics/query",
                    headers=headers,
                    params={
                        "metricSelector": "builtin:service.response.time:avg",
                        "entitySelector": f'type("SERVICE"),entityName("{service_name}")',
                        "from": f"now-{time_range_minutes}m",
                    },
                )
                if response.status_code == 200:
                    return json.dumps(response.json(), indent=2)
        except Exception:
            return None
        return None


class DynatraceProblemsInput(BaseModel):
    service_name: str = Field(..., description="Service name to inspect")
    status: str = Field(default="OPEN", description="Problem status filter")


class DynatraceProblemsTool(BaseTool):
    name: str = "dynatrace_problems"
    description: str = (
        "Returns Dynatrace problems and alert details for a service, including impact "
        "scope and likely root cause entity."
    )
    args_schema: Type[BaseModel] = DynatraceProblemsInput

    def _run(self, service_name: str, status: str = "OPEN") -> str:
        use_mock = os.getenv("USE_MOCK_INTEGRATIONS", "true").lower() == "true"
        if not use_mock:
            live = self._fetch_live(service_name, status)
            if live:
                return live
        return self._build_snapshot(service_name, status)

    def _build_snapshot(self, service_name: str, status: str) -> str:
        now = datetime.utcnow()
        payload = {
            "source": "dynatrace_problems",
            "service": service_name,
            "status_filter": status,
            "problems": [
                {
                    "problem_id": "P-INC-2401",
                    "title": f"High error rate on {service_name}",
                    "severity": "AVAILABILITY",
                    "status": "OPEN",
                    "start_time": (now - timedelta(minutes=42)).isoformat(),
                    "impact": "SERVICE",
                    "affected_entities": [service_name, "payment-db-primary"],
                    "root_cause_entity": "payment-db-primary",
                    "description": "Error rate crossed the critical threshold",
                }
            ],
        }
        return json.dumps(payload, indent=2)

    def _fetch_live(self, service_name: str, status: str):
        import httpx

        api_url = os.getenv("DYNATRACE_API_URL", "")
        api_token = os.getenv("DYNATRACE_API_TOKEN", "")
        if not api_url or not api_token:
            return None

        headers = {"Authorization": f"Api-Token {api_token}"}
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"{api_url}/api/v2/problems",
                    headers=headers,
                    params={"problemSelector": f'status("{status}")'},
                )
                if response.status_code == 200:
                    return json.dumps(response.json(), indent=2)
        except Exception:
            return None
        return None

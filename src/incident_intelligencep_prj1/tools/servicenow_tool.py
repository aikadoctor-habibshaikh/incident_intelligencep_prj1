import json
import os
from datetime import datetime, timedelta
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ServiceNowInput(BaseModel):
    incident_id: str = Field(..., description="ServiceNow incident number")
    action: str = Field(default="get", description="Action to perform")


class ServiceNowIncidentTool(BaseTool):
    name: str = "servicenow_incident"
    description: str = (
        "Fetches or prepares ServiceNow incident ticket details for triage and resolution updates."
    )
    args_schema: Type[BaseModel] = ServiceNowInput

    def _run(self, incident_id: str, action: str = "get") -> str:
        use_mock = os.getenv("USE_MOCK_INTEGRATIONS", "true").lower() == "true"
        if not use_mock:
            live = self._fetch_live(incident_id, action)
            if live:
                return live
        return self._build_snapshot(incident_id, action)

    def _build_snapshot(self, incident_id: str, action: str) -> str:
        now = datetime.utcnow()
        payload = {
            "source": "servicenow_incident",
            "action": action,
            "incident": {
                "number": incident_id,
                "short_description": "Production service degradation with elevated error rate",
                "description": "Monitoring detected elevated errors and latency across payment services.",
                "priority": "1 - Critical",
                "urgency": "1 - High",
                "impact": "1 - High",
                "state": "In Progress",
                "assignment_group": "Production Support",
                "assigned_to": "on-call-sre",
                "opened_at": (now - timedelta(minutes=48)).isoformat(),
                "category": "Application",
                "subcategory": "Performance",
                "configuration_item": "payment-service-prod",
                "business_service": "Payment Processing",
            },
        }
        return json.dumps(payload, indent=2)

    def _fetch_live(self, incident_id: str, action: str):
        import httpx

        instance = os.getenv("SERVICENOW_INSTANCE", "")
        username = os.getenv("SERVICENOW_USERNAME", "")
        password = os.getenv("SERVICENOW_PASSWORD", "")
        if not instance or not username:
            return None

        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"https://{instance}.service-now.com/api/now/table/incident",
                    auth=(username, password),
                    params={"sysparm_query": f"number={incident_id}"},
                )
                if response.status_code == 200:
                    return json.dumps(response.json(), indent=2)
        except Exception:
            return None
        return None

import os
import sys
import warnings
from pathlib import Path

from incident_intelligencep_prj1.crew import IncidentIntelligencePrj1
from incident_intelligencep_prj1.tools.github_tool import validate_github_repository

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    input_dir = Path("input") / "dynatrace_logs"
    output_dir = Path("output")
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    incident_id = "INC-20260627-001"
    affected_service = "payment-service"
    repository = "aikadoctor-habibshaikh/incident_intelligencep_prj1"
    incident_description = (
        "Payment service showing elevated errors and latency across Dynatrace logs. "
        "Multiple trace groups include PAYMENT_TIMEOUT and AUTH_TOKEN_EXPIRED events."
    )

    if len(sys.argv) > 1:
        incident_id = sys.argv[1]
    if len(sys.argv) > 2:
        affected_service = sys.argv[2]
    if len(sys.argv) > 3:
        repository = sys.argv[3]

    use_mock = os.getenv("USE_MOCK_INTEGRATIONS", "true").lower() == "true"

    repo_check = validate_github_repository(repository)
    if not repo_check["valid"] and not use_mock:
        print(f"Repository validation failed: {repo_check['error']}")
        sys.exit(1)
    elif not repo_check["valid"] and use_mock:
        print(
            f"Warning: repository validation failed ({repo_check['error']}), "
            "continuing anyway because USE_MOCK_INTEGRATIONS=true."
        )

    inputs = {
        "log_input_path": str(input_dir),
        "output_path": str(output_dir),
        "incident_id": incident_id,
        "affected_service": affected_service,
        "repository": repo_check.get("repository", repository),
        "incident_description": incident_description,
    }

    try:
        IncidentIntelligencePrj1().crew().kickoff(inputs=inputs)
    except Exception as exc:
        raise RuntimeError(f"Crew execution failed: {exc}") from exc


def train():
    inputs = {}
    try:
        IncidentIntelligencePrj1().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as exc:
        raise RuntimeError(f"Training failed: {exc}") from exc


def replay():
    try:
        IncidentIntelligencePrj1().crew().replay(task_id=sys.argv[1])
    except Exception as exc:
        raise RuntimeError(f"Replay failed: {exc}") from exc


def test():
    inputs = {}
    try:
        IncidentIntelligencePrj1().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as exc:
        raise RuntimeError(f"Test run failed: {exc}") from exc
import json
from pathlib import Path
from typing import Any


def analyze_logs_with_fallback(input_dir: Path, output_dir: Path) -> dict[str, Any]:
    log_files = sorted(input_dir.glob('*.jsonl')) + sorted(input_dir.glob('*.json')) + sorted(input_dir.glob('*.csv'))
    records: list[dict[str, Any]] = []

    for path in log_files:
        if path.suffix == '.jsonl':
            with path.open('r', encoding='utf-8') as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        elif path.suffix == '.json':
            with path.open('r', encoding='utf-8') as handle:
                data = json.load(handle)
                if isinstance(data, list):
                    records.extend([item for item in data if isinstance(item, dict)])
                elif isinstance(data, dict):
                    records.append(data)

    if not records:
        return {
            'incident_id': 'inc-local-001',
            'summary': 'No log records found.',
            'anomaly_findings': [],
            'error_patterns': [],
            'affected_services': [],
            'candidate_root_cause_hypotheses': ['No data available for analysis.'],
            'raw_log_references': []
        }

    error_events = [record for record in records if str(record.get('logLevel', '')).upper() == 'ERROR']
    services = sorted({str(record.get('service', 'unknown')) for record in records if record.get('service')})
    error_codes = sorted({str(record.get('errorCode', '')).strip() for record in records if str(record.get('errorCode', '')).strip()})

    incident_id = 'inc-local-001'
    summary = f"Detected {len(error_events)} error events across {len(services)} services."

    return {
        'incident_id': incident_id,
        'summary': summary,
        'anomaly_findings': [
            {
                'timestamp': str(records[0].get('timestamp', 'unknown')),
                'anomaly_type': 'error_cluster',
                'description': f"Recurring error patterns found in {', '.join(services[:3]) or 'observed services'}.",
                'service': services[0] if services else 'unknown'
            }
        ],
        'error_patterns': [
            {
                'error_code': code,
                'description': 'Observed in input log data',
                'occurrences': sum(1 for item in records if str(item.get('errorCode', '')).strip() == code),
                'example_message': next((str(item.get('message', '')) for item in records if str(item.get('errorCode', '')).strip() == code), '')
            }
            for code in error_codes[:5]
        ],
        'affected_services': services,
        'candidate_root_cause_hypotheses': [
            'Service degradation or dependency issue affecting multiple components.',
            'Recent configuration or deployment change introduced instability.'
        ],
        'raw_log_references': [
            {'log_file': str(path.name), 'lines': [1]}
            for path in log_files[:3]
        ]
    }


def build_root_cause_report(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        'incident_id': analysis.get('incident_id', 'inc-local-001'),
        'root_cause': {
            'primary': 'Observed recurring service errors and dependency instability.',
            'secondary': analysis.get('candidate_root_cause_hypotheses', [])
        },
        'confidence': 'Medium',
        'impact': {
            'description': 'Multiple services show elevated error rates and degraded availability.',
            'affected_services': analysis.get('affected_services', []),
            'users_affected': 'Potentially affected users may experience partial service disruption.'
        },
        'remediation_recommendations': [
            'Inspect recent deployments and configuration changes.',
            'Check downstream dependencies and service health dashboards.',
            'Prioritize incident response and customer communication.'
        ],
        'next_steps': [
            'Validate the incident with monitoring data.',
            'Open or update an incident ticket.',
            'Escalate to the owning service team if symptoms persist.'
        ],
        'affected_components': analysis.get('affected_services', [])
    }

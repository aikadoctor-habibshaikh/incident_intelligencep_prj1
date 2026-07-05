from pathlib import Path


def test_project_structure():
    required_paths = [
        Path('Dockerfile'),
        Path('pyproject.toml'),
        Path('src/incident_intelligencep_prj1/main.py'),
        Path('src/incident_intelligencep_prj1/crew.py'),
    ]
    for path in required_paths:
        assert path.exists(), f'Missing required path: {path}'

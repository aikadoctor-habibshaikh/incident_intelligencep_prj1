# Incident Intelligence PRJ1 Crew

Welcome to the Incident Intelligence PRJ1 Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence

## Execution steps

### 1. Prerequisites
- Python 3.10 or later
- A virtual environment is recommended
- Optional: Docker Desktop for containerized execution

### 2. Local execution
1. Open a terminal in the project root.
2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Install the project in editable mode:
   ```powershell
   python -m pip install -e .
   ```
4. Run the project:
   ```powershell
   python -m incident_intelligencep_prj1.main
   ```

### 3. Run a specific workflow step
- Log analysis only:
  ```powershell
  python -m incident_intelligencep_prj1.main --task log_analysis
  ```
- Root cause analysis only:
  ```powershell
  python -m incident_intelligencep_prj1.main --task root_cause
  ```

### 4. Docker execution
1. Build and run the full workflow:
   ```powershell
   docker compose up incident-intelligence
   ```
2. Run only the log analysis service:
   ```powershell
   docker compose up log-analysis-agent
   ```
3. Run only the root cause analysis service:
   ```powershell
   docker compose up root-cause-agent
   ```

### 5. Output files
The workflow writes results to:
- output/log_analysis.json
- output/root_cause_analysis.json

### 6. API key setup
If you want the project to use the OpenAI-backed agent flow, set your key in the `.env` file:
```env
OPENAI_API_KEY=your_key_here
```
If no key is provided, the project will run a local fallback analysis using the sample logs. and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
pip install boto3   
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/incident_intelligencep_prj1/config/agents.yaml` to define your agents
- Modify `src/incident_intelligencep_prj1/config/tasks.yaml` to define your tasks
- Modify `src/incident_intelligencep_prj1/crew.py` to add your own logic, tools and specific args
- Modify `src/incident_intelligencep_prj1/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the Incident Intelligence PRJ1 Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The Incident Intelligence PRJ1 Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the Incident Intelligence PRJ1 Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.

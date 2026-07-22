import os
from dotenv import load_dotenv

load_dotenv()

from typing import List

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from incident_intelligencep_prj1.tools.dynatrace_tool import DynatraceMetricsTool, DynatraceProblemsTool
from incident_intelligencep_prj1.tools.github_tool import GitHubDeploymentTool
from incident_intelligencep_prj1.tools.log_reader_tool import LogReaderTool
from incident_intelligencep_prj1.tools.servicenow_tool import ServiceNowIncidentTool


def build_llm() -> LLM:
    model = os.getenv("MODEL", "gemini/gemini-2.5-flash")
    return LLM(
        model=model,
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        num_retries=int(os.getenv("LLM_NUM_RETRIES", "5")),
    )


@CrewBase
class IncidentIntelligencePrj1:
    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        self.llm = build_llm()
        self.log_reader = LogReaderTool()
        self.dynatrace_metrics = DynatraceMetricsTool()
        self.dynatrace_problems = DynatraceProblemsTool()
        self.github_deployments = GitHubDeploymentTool()
        self.servicenow_incident = ServiceNowIncidentTool()

    @agent
    def incident_triage_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["incident_triage_agent"],
            llm=self.llm,
            tools=[self.log_reader, self.dynatrace_problems, self.servicenow_incident],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def log_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["log_analysis_agent"],
            llm=self.llm,
            tools=[self.log_reader],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def deployment_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["deployment_analysis_agent"],
            llm=self.llm,
            tools=[self.github_deployments],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def infrastructure_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["infrastructure_agent"],
            llm=self.llm,
            tools=[self.dynatrace_metrics, self.dynatrace_problems],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def root_cause_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["root_cause_analysis_agent"],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def resolution_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["resolution_agent"],
            llm=self.llm,
            tools=[self.servicenow_incident],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @task
    def triage_task(self) -> Task:
        return Task(
            config=self.tasks_config["triage_task"],
            output_file="output/triage.json",
        )

    @task
    def log_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["log_analysis_task"],
            output_file="output/log_analysis.json",
        )

    @task
    def deployment_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["deployment_analysis_task"],
            output_file="output/deployment_analysis.json",
        )

    @task
    def infrastructure_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["infrastructure_analysis_task"],
            output_file="output/infrastructure_analysis.json",
        )

    @task
    def root_cause_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["root_cause_analysis_task"],
            output_file="output/root_cause_analysis.json",
        )

    @task
    def resolution_task(self) -> Task:
        return Task(
            config=self.tasks_config["resolution_task"],
            output_file="output/resolution.json",
        )

    @crew
    def crew(self) -> Crew:
        ordered_tasks = [
            self.triage_task(),
            self.log_analysis_task(),
            self.deployment_analysis_task(),
            self.infrastructure_analysis_task(),
            self.root_cause_analysis_task(),
            self.resolution_task(),
        ]
        return Crew(
            agents=self.agents,
            tasks=ordered_tasks,
            process=Process.sequential,
            verbose=True,
        )
        
        
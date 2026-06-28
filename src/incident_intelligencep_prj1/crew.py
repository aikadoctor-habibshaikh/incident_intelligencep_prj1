from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class IncidentIntelligencePrj1():
    """Incident Intelligence PRJ1 crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def log_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['log_analysis_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def root_cause_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['root_cause_analysis_agent'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def log_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['log_analysis_task'], # type: ignore[index]
            output_file='output/log_analysis.json'
        )

    @task
    def root_cause_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['root_cause_analysis_task'], # type: ignore[index]
            output_file='output/root_cause_analysis.json'
        )

    def build_crew(self, task_name: str | None = None) -> Crew:
        """Creates the Incident Intelligence PRJ1 crew for the requested workflow step."""
        agents = [self.log_analysis_agent(), self.root_cause_analysis_agent()]

        if task_name == 'log_analysis':
            ordered_tasks = [self.log_analysis_task()]
        elif task_name == 'root_cause':
            ordered_tasks = [self.root_cause_analysis_task()]
        else:
            ordered_tasks = [
                self.log_analysis_task(),
                self.root_cause_analysis_task(),
            ]

        return Crew(
            agents=agents,
            tasks=ordered_tasks,
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Incident Intelligence PRJ1 crew"""
        return self.build_crew()

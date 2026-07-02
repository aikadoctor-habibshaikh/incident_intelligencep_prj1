from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
from log_analyst.tools import MyLogAnalystTool


@CrewBase
class LogAnalyst:
    """LogAnalyst crew"""

    agents: list[Agent]
    tasks: list[Task]

    ''' def __init__(self, log_file_path=None):
        self.assignment = assignment
        self.log_file_path = log_file_path '''

    @agent
    def log_analyser(self) -> Agent:
        return Agent(
            config=self.agents_config['log_analyser'],  # must match agents.yaml
            verbose=True,
            tools=[MyLogAnalystTool()]
        )

    @task
    def log_analyser_task(self) -> Task:
        return Task(
            config=self.tasks_config['log_analyser_task'],  # must match tasks.yaml
            output_file='log_report.txt',
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LogAnalyst crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


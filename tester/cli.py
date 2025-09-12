import click
from tester.agent import Agent

@click.group()
def cli():
    pass

@cli.command()
@click.argument('target')
def run(target):
    agent = Agent(target)
    agent.run()
import click
from tester.agent import Agent
from tester.utils.config import config

@click.group()
@click.version_option(version="0.1.0", prog_name="tester")
def cli():
    pass

@cli.command()
@click.argument('target')
@click.option('--max-steps', default=10, help='Maximum number of steps for the agent to run')
def run(target, max_steps):
    agent = Agent()
    agent.run(target, max_steps)

@cli.command()
@click.argument('topic', required=False)
def help(topic):
    if not topic:
        show_general_help()
    elif topic.lower() == 'config':
        show_config_help()
    else:
        click.echo(f"Unknown help topic: {topic}")
        click.echo("Available topics: tools, config, examples, architecture")

def show_general_help():
    help_text = """
Tester - AI-Powered Security Assessment Tool

DESCRIPTION:
    Tester is an automated security testing tool that uses AI agents to perform
    penetration testing and vulnerability assessments. It runs in a containerized
    environment and can execute various security tools and techniques.

USAGE:
    tester [OPTIONS] COMMAND [ARGS]...

COMMANDS:
    run     Run security assessment on a target
    help    Show detailed help information

GETTING STARTED:
    1. Configure your environment (see 'tester help config')
    2. Run an assessment: tester run http://example.com
    3. Review the results and agent actions

For more detailed help, use:
    tester help <topic>  where topic is: config
"""
    click.echo(help_text)

def show_config_help():
    help_text = f"""
Configuration Guide

CONFIGURATION FILE: config.toml

Current Configuration:
    Runtime Image: {config.runtime.image_name}:{config.runtime.image_tag}
    Container Name: {config.runtime.container_name}
    Network: {config.runtime.network_name}
    Memory Limit: {config.runtime.mem_limit}
    
    AI Source: {config.agent.source}
    Google Model: {config.agent.google_model}
    OpenAI Model: {config.agent.openai_model}

ENVIRONMENT VARIABLES:
    Set these in your .env file or environment:
    
    For Google AI:
    - GOOGLE_API_KEY - Your Google AI API key
    
    For OpenAI:
    - OPENAI_API_KEY - Your OpenAI API key
    
    For Local Models:
    - Model path configured in config.tomlt

SETUP STEPS:
    1. Copy config.toml.example to config.toml (if available)
    2. Set your preferred AI source in config.toml
    3. Set the appropriate API key in .env
    4. Ensure Docker is running
    5. Run your first assessment
"""
    click.echo(help_text)



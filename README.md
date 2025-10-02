# Agentic Testing Framework

## Project Overview
The Agentic Testing Framework is designed to facilitate automated security testing of web applications.

### Agent Workflow
1. **System Prompt**: Defines the overall behavior and objectives of the agent.
2. **Tool Usage**: The agent can utilize various tools to perform specific tasks.
3. **Human Approval**: Each tool request is subject to human approval before execution.
4. **Execution**: Approved tool requests are executed, and results are returned to the agent.
5. **Iteration**: The agent iteratively refines its approach based on results and feedback

## Useful Commands
- Start lab environment:
  ```bash
  sudo docker-compose -f lab/docker-compose.dvwa.yml up -d
  ```
- Build Docker Image:
  ```bash
  docker build -t <image_name>:<image_tag> .
  ```
- Run tester on lab environment:
  ```bash
  tester run http://dvwa:80
  ```
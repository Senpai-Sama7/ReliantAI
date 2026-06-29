"""
CLI entry point for agents-cli.

Usage:
    agents-cli start          # Start all agents
    agents-cli start prospector  # Start specific agent
    agents-cli status         # Show agent status
    agents-cli stop           # Stop all agents
    agents-cli health         # Health check all agents
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Any

import click
import structlog

from .. import setup_logging
from ..core import get_logger

logger = get_logger("agents.cli")


def get_available_agents() -> dict[str, Any]:
    """Return all available agent classes."""
    from ..workers.prospector import ProspectingAgent
    from ..workers.outreach import OutreachAgent
    from ..workers.followup import FollowupAgent
    from ..workers.site_builder import SiteBuilderAgent

    return {
        "prospector": ProspectingAgent,
        "outreach": OutreachAgent,
        "followup": FollowupAgent,
        "site_builder": SiteBuilderAgent,
    }


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
@click.option("--log-file", default=None, help="Log file path")
@click.option("--json-log/--no-json-log", default=True, help="JSON format logging")
def cli(log_level: str, log_file: str | None, json_log: bool):
    """ReliantAI Agents CLI — autonomous 24/7 agent system."""
    setup_logging(level=log_level, log_file=log_file, json_format=json_log)


@cli.command()
@click.argument("agent_name", required=False)
@click.option("--foreground/--daemon", default=True, help="Run in foreground")
def start(agent_name: str | None, foreground: bool):
    """Start agents. If no name given, start all."""
    agents = get_available_agents()

    if agent_name and agent_name not in agents:
        click.echo(f"Unknown agent: {agent_name}. Available: {', '.join(agents.keys())}")
        sys.exit(1)

    to_start = {agent_name: agents[agent_name]} if agent_name else agents

    click.echo(f"Starting agents: {', '.join(to_start.keys())}")

    if not foreground:
        # Daemon mode — fork to background
        try:
            pid = os.fork()
            if pid > 0:
                click.echo(f"Daemon started (PID {pid})")
                sys.exit(0)
        except OSError as e:
            click.echo(f"Fork failed: {e}", err=True)
            sys.exit(1)

    # Run agents
    asyncio.run(_run_agents(to_start))


async def _run_agents(agent_map: dict[str, Any]):
    """Run all specified agents concurrently."""
    tasks = []
    agent_instances = []

    for name, cls in agent_map.items():
        agent = cls()
        agent_instances.append(agent)
        task = asyncio.create_task(agent.run(), name=f"agent-{name}")
        tasks.append(task)
        logger.info("agent_task_created", agent=name)

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _shutdown(signum, frame):
        logger.info("shutdown_signal", signal=signum)
        for agent in agent_instances:
            agent.stop()
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Wait for all agents to complete or stop signal
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        pass

    logger.info("all_agents_stopped")


@cli.command()
def status():
    """Show status of all agents."""
    click.echo("Agent status: TODO — connect to running daemon via IPC")


@cli.command()
def health():
    """Run health checks."""
    click.echo("Health check: TODO — connect to running daemon via IPC")


@cli.command()
def stop():
    """Stop all running agents."""
    click.echo("Stop: TODO — send signal to running daemon")


@cli.command()
@click.option("--output", "-o", default="docker-compose.agents.yml", help="Output file")
def generate_docker_compose(output: str):
    """Generate Docker Compose file for deploying agents."""
    compose = """version: '3.8'
services:
  agents-daemon:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
      - GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - TWILIO_FROM_NUMBER=${TWILIO_FROM_NUMBER}
      - RESEND_API_KEY=${RESEND_API_KEY}
      - DATABASE_URL=postgresql://reliantai:reliantai_dev@postgres:5432/reliantai
      - REDIS_URL=redis://redis:6379/0
      - API_SECRET_KEY=${API_SECRET_KEY}
      - AGENTS_LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - agent-data:/home/agent/.local/share/reliantai

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: reliantai
      POSTGRES_USER: reliantai
      POSTGRES_PASSWORD: reliantai_dev
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U reliantai"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass reliantai_dev --maxmemory 256mb
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "reliantai_dev", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
  redisdata:
  agent-data:
"""
    with open(output, "w") as f:
        f.write(compose)
    click.echo(f"Generated {output}")


if __name__ == "__main__":
    cli()

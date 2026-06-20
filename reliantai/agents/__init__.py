"""
ReliantAI Agents CLI - Autonomous 24/7 agent system.

Maximizes profit by continuously:
1. Finding new prospects (Google Places API)
2. Researching businesses (GBP, PageSpeed, reviews)
3. Generating high-converting website copy
4. Building and registering preview sites
5. Sending personalized outreach (SMS + email)
6. Following up with non-responders
7. Tracking hot leads and notifying the owner
"""

__version__ = "1.0.0"

from .core import setup_logging, get_logger, Telemetry  # noqa: F401

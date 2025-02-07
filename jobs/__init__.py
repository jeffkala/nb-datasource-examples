"""Module for design jobs."""

from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.util import load_jobs

from .tcp_connectivity_check import ConnectivityCheckTask

load_jobs("jobs")
register_jobs(ConnectivityCheckTask,)
"""Module for design jobs."""

from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.util import load_jobs

from .tcp_connectivity_check import ConnectivityCheckTask
from .command_getter import CommandExecution
from .debug_nornir_inventory import DebugInventoryJob

load_jobs("jobs")
register_jobs(ConnectivityCheckTask, CommandExecution, DebugInventoryJob)

"""General Job Patterns."""

import time

from celery.exceptions import SoftTimeLimitExceeded
from nautobot.apps.jobs import IntegerVar, Job, ObjectVar, StringVar, register_jobs
from nautobot.dcim.models import Device

name = "General Job Patterns"


class SensitiveCredentialJob(Job):
    """Sensitive variable handling.

    Accepts a credential as input. Because ``has_sensitive_variables`` is True (the
    default), Nautobot does not store the input values with the JobResult. The Job
    never logs the credential value.
    """

    target = ObjectVar(
        description="Record to act on. Passed by primary key, re-read here.",
        model=Device,
    )
    secret = StringVar(description="A credential. Its value is never logged or stored.")

    class Meta:
        """Meta attributes."""

        name = "Sensitive credential (no logging)"
        description = "Demonstrates sensitive variable handling; the input is not stored or logged."
        task_queues = ["celery-standard"]
        # Left at the default True so input values are not saved to the database.
        has_sensitive_variables = True

    def run(self, target, secret):  # pylint: disable=arguments-differ
        """Use the credential without logging it."""
        # Never log `secret` or place it in an exception message (HLD 15.4).
        self.logger.info("Received a credential of length %d for %s.", len(secret), target.name)
        self.logger.success("Acted on %s without exposing the credential.", target.name, extra={"object": target})
        return "ok"


class HelloLatencyJob(Job):
    """Latency-sensitive Job.

    A trivial, fast Job. A requester waits for the result, so it declares a short
    soft time limit and targets the dedicated latency queue. The same Job code
    runs unchanged on any queue type.
    """

    class Meta:
        """Meta attributes."""

        name = "Hello (latency-sensitive)"
        description = "Fast demonstration Job for the latency-sensitive class."
        soft_time_limit = 10
        time_limit = 20
        has_sensitive_variables = False

    def run(self):  # pylint: disable=arguments-differ
        """Log a single line and return."""
        self.logger.info("Hello from the latency-sensitive queue.")
        return "ok"


class LongRunningReportJob(Job):
    """Long-running Job with checkpointing.

    Runs several phases. It reports progress at each phase boundary, not per item.
    It catches the soft-time-limit exception so it can record where it
    stopped before the hard limit ends the process. Nautobot's Cancel
    action is a hard kill, so the soft time limit is the only cooperative
    interruption point.
    """

    phases = IntegerVar(description="Number of phases to run.", default=5, min_value=1, max_value=50)

    class Meta:
        """Meta attributes."""

        name = "Long-running report (checkpointed)"
        description = "Phase-based long Job that checkpoints progress and handles the soft time limit."
        soft_time_limit = 60
        time_limit = 120
        has_sensitive_variables = False

    def run(self, phases):  # pylint: disable=arguments-differ
        """Run the phases, checkpointing after each one."""
        completed = 0
        try:
            for phase in range(1, phases + 1):
                time.sleep(1)  # Stand-in for real work.
                completed = phase
                # Checkpoint at the phase boundary (HLD 8.4).
                self.logger.info("Completed phase %d of %d.", phase, phases)
        except SoftTimeLimitExceeded:
            # Record the checkpoint before the hard limit stops the process (HLD 8.1).
            self.logger.warning("Soft time limit reached. Completed %d of %d phases.", completed, phases)
            return {"completed_phases": completed, "interrupted": True}

        self.logger.success("All %d phases complete.", phases)
        return {"completed_phases": completed, "interrupted": False}


class SingletonMaintenanceJob(Job):
    """Singleton Job.

    Only one instance may run at a time. Nautobot enforces this with a Redis lock
    keyed on the Job, set to time out on the hard time limit. A second concurrent
    run fails with a singleton error instead of duplicating the work.
    """

    class Meta:
        """Meta attributes."""

        name = "Singleton maintenance"
        description = "Demonstrates whole-Job mutual exclusion with is_singleton."
        is_singleton = True
        soft_time_limit = 60
        time_limit = 120
        has_sensitive_variables = False

    def run(self):  # pylint: disable=arguments-differ
        """Simulate exclusive maintenance work."""
        self.logger.info("Singleton maintenance started; no other instance can run now.")
        time.sleep(5)
        self.logger.success("Singleton maintenance finished.")


register_jobs(
    HelloLatencyJob,
    LongRunningReportJob,
    SingletonMaintenanceJob,
    SensitiveCredentialJob,
)

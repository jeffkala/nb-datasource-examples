"""Jobs Demonstrating Python ThreadPool."""

import time
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections
from nautobot.apps.jobs import IntegerVar, Job, register_jobs
from nautobot.dcim.models import Device

name = "Python ThreadPool Example"


class InJobParallelFanOutJob(Job):
    """Fan-out by in-Job parallelism.

    This is the recommended fan-out method: one Job processes the whole target
    set with an internal bounded thread pool, holds the outcome in one JobResult,
    and reports one consolidated result with counts by outcome. The
    ``max_workers`` value is the backpressure control. Each worker thread
    closes its database connection so the pool does not leak connections.
    """

    max_workers = IntegerVar(
        description="Concurrent workers. This is the backpressure limit.",
        default=4,
        min_value=1,
        max_value=16,
    )
    failure_threshold_percent = IntegerVar(
        description="Stop reporting success if the failure rate exceeds this percentage.",
        default=25,
        min_value=1,
        max_value=100,
    )

    class Meta:
        """Meta attributes."""

        name = "Fan-out: in-Job parallelism (recommended)"
        description = "Processes the target set with a bounded thread pool inside one Job."
        soft_time_limit = 600
        time_limit = 660
        has_sensitive_variables = False

    @staticmethod
    def _process_one(record):
        """Process one item. Returns True on success. Runs in a worker thread."""
        try:
            # record = Device.objects.get(pk=pk)
            # Stand-in for real per-item work (e.g. a device call).
            record.serial = "in job fanout"
            record.validated_save()
            return True
        except Exception:  # pylint: disable=broad-except
            return False
        finally:
            # Threads get their own DB connections; close them so the pool does not leak.
            close_old_connections()

    def run(self, max_workers, failure_threshold_percent):  # pylint: disable=arguments-differ
        """Resolve the target set once, then process it concurrently."""
        # Resolve the target set once, pass only primary keys to the workers.
        # pks = list(Device.objects.values_list("pk", flat=True))
        devices = Device.objects.all()
        # if not pks:
        #     self.logger.warning("No example records exist. Run 'Populate example models' first.")
        #     return {"total": 0, "succeeded": 0, "failed": 0}

        # succeeded = 0
        # failed = 0
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(self._process_one, pk): pk for pk in devices}
        elapsed = time.perf_counter() - start
        self.logger.info(f"{elapsed:.4f} seconds")
        # for future in as_completed(futures):
        #     if future.result():

        #         succeeded += 1
        #     else:
        #         failed += 1

        # total = len(pks)
        # failure_rate = (failed / total) * 100
        # # Consolidated outcome with counts.
        # self.logger.info("Fan-out complete. total=%d succeeded=%d failed=%d", total, succeeded, failed)
        # if failure_rate > failure_threshold_percent:
        #     # Threshold partial-failure mode..
        #     self.logger.error(
        #         "Failure rate %.1f%% exceeds the %d%% threshold. Treat as a systemic failure.",
        #         failure_rate,
        #         failure_threshold_percent,
        #     )
        # return {"total": total, "succeeded": succeeded, "failed": failed}


register_jobs(InJobParallelFanOutJob)

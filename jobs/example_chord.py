import time

from celery import chord
from django.core.cache import cache
from nautobot.apps.jobs import Job, StringVar, register_jobs
from nautobot.core.celery import nautobot_task
from nautobot.dcim.models import Device

name = "Celery Chord Example"


@nautobot_task
def process_item(device_name):
    """Example parallel task."""
    item_name = Device.objects.get(name=device_name)
    item_name.serial = "updated from chord"
    item_name.validated_save()
    return {
        "item": device_name,
        "status": "success",
        "details": f"Processed {device_name}",
    }


@nautobot_task
def aggregate_results(results, job_result_id, username, batch_name):
    """Chord callback."""
    summary = {
        "job_result_id": job_result_id,
        "requested_by": username,
        "batch_name": batch_name,
        "total": len(results),
        "successful": sum(1 for r in results if r.get("status") == "success"),
        "failed": sum(1 for r in results if r.get("status") != "success"),
        "results": results,
    }

    cache.set(f"nautobot-job-chord-summary:{job_result_id}", summary, timeout=3600)
    return summary


class LaunchChordJob(Job):
    batch_name = StringVar(
        description="Friendly name for this batch run.",
        default="example-batch",
    )

    class Meta:
        name = "Launch Celery Chord"
        description = "Example Nautobot Job using a Celery chord safely"

    def run(self, *, batch_name):
        items = Device.objects.all()
        self.logger.info("Launching chord for %s items", items.count())
        # start = time.perf_counter()
        # for item_name in items:
        #     item_name.serial = "pre sn"
        #     item_name.validated_save()
        # elapsed = time.perf_counter() - start
        # self.logger.info(f"{elapsed:.4f} seconds")
        start = time.perf_counter()
        header = [process_item.s(item_name.name) for item_name in items]
        callback = aggregate_results.s(
            str(self.job_result.id),
            self.user.username,
            batch_name,
        )
        async_result = chord(header)(callback)
        elapsed = time.perf_counter() - start
        self.logger.info(f"{elapsed:.4f} seconds")
        self.logger.info(
            "Submitted chord for JobResult %s with callback task id %s",
            self.job_result.id,
            async_result.id,
        )

        cache.set(
            f"nautobot-job-chord-task:{self.job_result.id}",
            {
                "job_result_id": str(self.job_result.id),
                "batch_name": batch_name,
                "callback_task_id": async_result.id,
                "items": list(items),
                "status": "submitted",
            },
            timeout=3600,
        )

        return {
            "message": "Chord submitted successfully.",
            "job_result_id": str(self.job_result.id),
            "callback_task_id": async_result.id,
            "summary_cache_key": f"nautobot-job-chord-summary:{self.job_result.id}",
        }


register_jobs(LaunchChordJob)

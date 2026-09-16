"""Parent-to-child Fan-out Example."""

from nautobot.apps.jobs import IntegerVar, Job, StringVar, register_jobs
from nautobot.dcim.models import Device
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models import JobResult

name = "Parent-to-child Fan-out Example"


class FanOutChildJob(Job):
    """Child Job for the parent-to-child fan-out (secondary pattern).

    Processes one unit and reports. It has its own JobResult, so it is
    independently visible, cancellable, and re-runnable. A child Job must never
    start a further fan-out (two levels only).
    """

    item_pk = StringVar(description="Primary key of the record to process.")
    parent_job_result_id = StringVar(
        description="JobResult ID of the parent, for manual linkage (HLD 7.4).",
        default="",
        required=False,
    )

    class Meta:
        """Meta attributes."""

        name = "Fan-out child"
        description = "Processes one unit as its own JobResult. Dispatched by the fan-out parent."
        soft_time_limit = 120
        time_limit = 180
        has_sensitive_variables = False
        # Not shown in the main Jobs list; it is invoked by the parent.
        hidden = True

    def run(self, item_pk, parent_job_result_id=""):  # pylint: disable=arguments-differ
        """Process the single record identified by ``item_pk``."""
        if parent_job_result_id:
            self.logger.info("Child of parent JobResult %s.", parent_job_result_id)
        # Re-read the object at the start of run(); handle a deleted record.
        try:
            record = Device.objects.get(pk=item_pk)
        except Device.DoesNotExist:
            self.logger.warning("Record %s no longer exists; nothing to do.", item_pk)
            return "skipped"
        record.description = f"{record.name} processed by child"
        record.validated_save()
        self.logger.success("Processed %s.", record.name, extra={"object": record})
        return "ok"


class FanOutParentJob(Job):
    """Parent-to-child fan-out (Secondary pattern).

    Dispatches one child Job per unit. This pattern is NOT a built-in Nautobot
    feature: the parent-child linkage is manual
    (the parent writes child JobResult primary keys to its log), and
    there is no built-in aggregation. This parent is fire-and-forget: it does not
    wait for the children, so it does not hold a worker slot. ``max_children`` is
    the in-flight limit that the parent owns. Prefer
    ``InJobParallelFanOutJob`` unless each unit truly needs its own JobResult.
    """

    max_children = IntegerVar(
        description="In-flight limit. The parent owns this admission control.",
        default=10,
        min_value=1,
        max_value=100,
    )

    class Meta:
        """Meta attributes."""

        name = "Fan-out: parent-to-child (use only when needed)"
        description = "Dispatches one child Job per unit. Linkage and aggregation are custom."
        soft_time_limit = 300
        time_limit = 360
        has_sensitive_variables = False

    def run(self, max_children):  # pylint: disable=arguments-differ
        """Dispatch up to ``max_children`` child Jobs, one per record."""
        child_job_model = JobModel.objects.get(
            module_name="jobs.jobs",
            job_class_name="FanOutChildJob",
        )
        if not child_job_model.enabled:
            self.logger.error("Child Job is not enabled. Enable 'Fan-out child' before running this parent.")
            return {"dispatched": 0}

        pks = list(Device.objects.values_list("pk", flat=True)[:max_children])
        if not pks:
            self.logger.warning("No example records exist. Run 'Populate example models' first.")
            return {"dispatched": 0}

        dispatched = []
        for pk in pks:
            child_result = JobResult.enqueue_job(
                child_job_model,
                self.user,
                str(pk),
                job_kwargs={"parent_job_result_id": str(self.job_result.pk)},
            )
            # Manual parent-to-child linkage (HLD 7.4): record the child JobResult IDs.
            dispatched.append(str(child_result.pk))

        self.logger.info("Dispatched %d child Jobs (in-flight limit %d).", len(dispatched), max_children)
        self.logger.info("Child JobResult IDs: %s", ", ".join(dispatched))
        return {"dispatched": len(dispatched), "child_job_result_ids": dispatched}


register_jobs(
    FanOutChildJob,
    FanOutParentJob,
)

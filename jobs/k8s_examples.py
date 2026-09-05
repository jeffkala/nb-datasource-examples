from nautobot.apps.jobs import BooleanVar, Job, StringVar, register_jobs
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models import JobQueue, JobResult

name = "Kubernetes Queue Examples"


class ChildJob(Job):
    target_name = StringVar(
        description="Target name to process.",
        default="example-target",
    )

    class Meta:
        name = "Child Job"
        description = "Example child job launched by another job."

    def run(self, *, target_name):
        self.logger.info("Child job running for target %s", target_name)
        return {
            "processed_target": target_name,
            "status": "success",
        }


class ParentLauncherJob(Job):
    target_name = StringVar(
        description="Target name to pass to the child job.",
        default="example-target",
    )
    submit_child_to_kubernetes = BooleanVar(
        default=True,
        description="If true, explicitly submit the child job to a Kubernetes JobQueue named 'kubernetes'.",
    )

    class Meta:
        name = "Parent Launcher Job"
        description = "Runs on Kubernetes and submits another Nautobot Job."
        queue_type = "kubernetes"

    def run(self, *, target_name, submit_child_to_kubernetes):
        self.logger.info(
            "Parent job started. Parent JobResult: %s",
            self.job_result.id,
        )

        # Update this class_path to match your actual file/module path. jobs_repo.jobs.k8s_examples.ParentLauncherJob
        child_job = JobModel.objects.get_for_class_path("jobs_repo.jobs.k8s_examples.ChildJob")

        job_queue = None
        if submit_child_to_kubernetes:
            try:
                job_queue = JobQueue.objects.get(name="kubernetes")
                self.logger.info("Using Kubernetes JobQueue '%s' for child job", job_queue.name)
            except JobQueue.DoesNotExist:
                self.logger.warning(
                    "Kubernetes JobQueue named 'kubernetes' was not found; child job will use default queue selection."
                )

        child_job_result = JobResult.enqueue_job(
            job_model=child_job,
            user=self.user,
            job_args=(target_name,),
            job_kwargs={},
            # job_kwargs={
            #     "target_name": target_name,
            # },
            job_queue=job_queue,
        )

        self.logger.success(
            "Submitted child job '%s' with JobResult %s",
            child_job.name,
            child_job_result.id,
        )

        return {
            "parent_job_result_id": str(self.job_result.id),
            "child_job_name": child_job.name,
            "child_job_result_id": str(child_job_result.id),
            "child_job_queue": job_queue.name if job_queue else "default",
            "message": "Child job submitted successfully.",
        }


register_jobs(ChildJob, ParentLauncherJob)

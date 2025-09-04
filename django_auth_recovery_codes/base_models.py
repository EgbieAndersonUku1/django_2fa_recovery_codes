from django.utils import timezone
from django.db import models
from datetime import timedelta
from django.conf import settings


class AbstractCleanUpScheduler(models.Model):
    """
    Abstract base model for scheduled cleanup tasks.

    This class defines common fields and behaviour that can be inherited by other
    models that implement scheduled cleanup logic. Using this base class avoids
    repeating the same fields and functionality across multiple models.

    Notes:
        - This is an abstract base class; Django does not create a database table for it.
        - Subclasses inherit all fields, methods, and Meta options defined here.
        - Default ordering or other Meta attributes can be overridden in subclasses.
        - Ideal for models that share scheduling, timestamp, or cleanup-related fields.

    Example:
        class EmailCleanupTask(AbstractCleanUpScheduler):
            recipient = models.EmailField()

            def perform_cleanup(self):
                # task-specific cleanup logic here
                pass
    """

    class Status(models.TextChoices):
        SUCCESS        = "s", "Success"
        FAILURE        = "f", "Failure"
        DELETED        = "d", "Deleted"
        PENDING        = "p", "Pending"

    class Schedule(models.TextChoices):
        ONCE      = "O", "Once"
        HOURLY    = "H", "Hourly"
        DAILY     = "D", "Daily"
        WEEKLY    = "W", "Weekly"
        MONTHLY   = "M", "Monthly"
        QUARTERLY = "Q", "Quarterly"  
        YEARLY    = "Y", "Yearly"

    name               = models.CharField(max_length=180, db_index=True, unique=True)
    enable_scheduler   = models.BooleanField(default=True)
    retention_days     = models.PositiveBigIntegerField(default=30)
    run_at             = models.DateTimeField()
    schedule_type      = models.CharField(max_length=1, choices=Schedule.choices, default=Schedule.DAILY, help_text="Select how often this task should run.")
    next_run           = models.DateTimeField(blank=True, null=True)
    deleted_count      = models.PositiveIntegerField(default=0)
    status             = models.CharField(max_length=1, choices=Status, default=Status.PENDING)
    error_message      = models.TextField(null=True, blank=True, editable=False)
    use_with_logger    = models.BooleanField(default=lambda: settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER or False, help_text=(
                                            "If True, the scheduler will use a logger to record the sending of emails. "
                                            "Default value comes from the setting "
                                            "'DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER'."
                                            )
                                    )

    class Meta:
        ordering = ['-run_at']
        abstract = True

    def __str__(self):
        return f"{self.run_at} - {self.status} - Deleted {self.deleted_count}, Is Scheduler Enabled: f{"True" if self.enable_scheduler else "False"}"

    @classmethod
    def get_schedulers(cls, enabled = True):
        return cls.objects.filter(enable_scheduler=enabled)
    
    @classmethod
    def get_by_scheduler_id(cls, scheduler_id: str):
        """"""
        try:
            return cls.objects.get(pk=scheduler_id)
        except cls.DoesNotExist:
            return None

    def next_run_schedule(self):
        """Decide the next run time based on schedule_type."""
        now = timezone.now()

        if self.schedule_type == self.Schedule.HOURLY:
            return now + timedelta(hours=1)
        elif self.schedule_type == self.Schedule.DAILY:
            return now + timedelta(days=1)
        elif self.schedule_type == self.Schedule.WEEKLY:
            return now + timedelta(weeks=1)
        elif self.schedule_type == self.Schedule.MONTHLY:
            return now + timedelta(days=30)  
        elif self.schedule_type == self.Schedule.QUARTERLY:
            return now + timedelta(days=90)
        elif self.schedule_type == self.Schedule.YEARLY:
            return now + timedelta(days=365)
        elif self.schedule_type == self.Schedule.ONCE:
            return now
        return None 
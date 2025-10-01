# 
# base_models.py

# Provides abstract base classes and utility functions for models
# that implement login attempt tracking, cooldowns, and rate-limiting
# behaviour. These classes are not meant to be instantiated directly,
# but extended by concrete models.
# 

import logging
from typing import Self
from datetime import timedelta
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from django_auth_recovery_codes.utils.cache.safe_cache import delete_cache_with_retry, get_cache_with_retry
from django_auth_recovery_codes.app_settings import default_cooldown_seconds, default_multiplier


User  = get_user_model()


def get_default_logger():
    from django.conf import settings
    return getattr(settings, "DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER", False)



class AbstractBaseModel(models.Model):
    """
    
    Abstract base model for reusable model functionality.

    Subclasses can inherit shared behaviour and utility methods defined here.
    For example, `get_by_user` provides a way to fetch a model instance
    associated with a given user, but additional shared methods can also be
    added as needed.

    Note:
    This is an abstract model and doesn't create a table in database.

    """
    class Meta:
        abstract = True

    @staticmethod
    def is_user_valid(user):
        """"""
        if not isinstance(user, User):
            raise TypeError(f"The user instance is not instance of User. Expected user to be an instance of user but got {type(user).__name__}")
        return True
    
    @classmethod
    def get_by_user_or_create(cls, user: User) -> Self:
        """
        Retrieve the instance associated with the given user, or create one if it does not exist.

        Args:
            user (User): The user to retrieve or create the instance for.

        Returns:
            Self: The instance linked to the provided user.
        """
        cls.is_user_valid(user)
        obj, _ = cls.objects.get_or_create(user=user)
        return obj

    @classmethod
    def get_by_user(cls, user: User) -> Self | None:
        """
        A method that uses the user instance to return a given model. 
        
        Note the model you want to return must have a user field within the model 
        either by ForeignKey, OneToOneField, ManyToManyField, etc 
        
        In situation where you want to perform additional operations before 
        returning the user e.g (get filtering by active post) you can override 
        the class behaviour by adding a method with the same name inside your
        class but with its own custom behaviour.
       
        Args:
            user (User): The user object to filter on.

        Raises:
            TypeError: If `user` is not an instance of `User`.

        Returns:
            Self | None: The model instance linked to the user, 
            or None if no match exists.

        Examples:
            Basic usage:
                >>> class Post(AbstractBaseModel):
                ...     user = models.ForeignKey(User, on_delete=models.CASCADE)
                ...
                >>> Post.get_by_user(user)
                <Post object>

            Overriding behaviour:
                >>> class Post(AbstractBaseModel):
                ...     user = models.ForeignKey(User, on_delete=models.CASCADE)
                ...     active = models.BooleanField(default=False)
                ...
                ...     @classmethod
                ...     def get_by_user(cls, user):
                ...         return cls.objects.filter(user=user, active=True)
        """
        if not isinstance(user, User):
            raise TypeError(f"Expected a User instance but got {type(user).__name__}")
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None


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
    use_with_logger    = models.BooleanField(default=get_default_logger, help_text=(
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
    def get_by_schedule_name(cls, schedule_name: str):
        """"""

        try:
            return cls.objects.get(name=schedule_name)
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
    


class AbstractCooldownPeriod(models.Model):
    last_attempt     = models.DateTimeField(auto_now=True)
    cooldown_seconds = models.PositiveSmallIntegerField(default=default_cooldown_seconds, 
                                                        help_text="The number of seconds before a new request can be made. Default " \
                                                        "valued used from the settings.DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN flag")
    multiplier        = models.PositiveSmallIntegerField(default=default_multiplier, 
                                                         help_text="The multiplier used to increase the wait time ." \
                                                         "Default value used from the settings.DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER flag")
    class Meta:
        abstract = True

    def __str__(self):
        return f"Cooldown seconds: {self.cooldown_seconds} and multiplie: {self.multiplier}"
     
    def _get_next_allowed_time_for_next_attempt(self):
        """"""
        return self.last_attempt + timedelta(seconds=self.cooldown_seconds)

    def get_remaining_time_till_next_attempt(self):
        """"""
        next_allowed_time = self._get_next_allowed_time_for_next_attempt()
        current_time_now  = timezone.now()

        return max(int((next_allowed_time - current_time_now).total_seconds()), 0)
    

def flush_cache_and_write_attempts_to_db(instance, field_name, cache_key: str, logger: logging.Logger = None):
    """
    Add cached attempts to the batch and clear cache.
    """
    if not isinstance(cache_key, str):
        raise ValueError(f"Expected the cache key to be a string but got a value with {type(cache_key).__name__}")
    
    if not isinstance(logger, logging.Logger):
        raise ValueError(f"Expected a Logger instance, got logger with {type(logger).__name__}")
    
    if not isinstance(field_name, str):
        raise ValueError(f"Expected the field name to be a string but got a value with {type(field_name).__name__}") 
    
    if not hasattr(instance, field_name):
        raise ValueError(f"This field name: '{field_name}' was not found in the instance model")
    
    data = get_cache_with_retry(cache_key, default={})
    
    try:
        logger.debug("Flushing cache: object_id=%s, key=%s, data=%s", getattr(instance, "id", None), cache_key, data)

        attempts = data.get("attempts", 0)
        if attempts > 0:

            setattr(instance, field_name, attempts)
            instance.save(update_fields=[field_name])

            logger.info(f"Persisted attempts: object_id={instance.id}, attempts={attempts}")
        else:
            logger.debug("No attempts to flush: object_id=%s, key=%s", getattr(instance, "id", None), cache_key)
            instance.save(update_fields=["last_attempt"])
            delete_cache_with_retry(cache_key)
            logger.debug("Cleared cache: object_id=%s, key=%s, data=%s", getattr(instance, "id", None), cache_key, data)

    except Exception as e:
        logger.exception("Failed in do_something")
        delete_cache_with_retry(cache_key)
        raise RuntimeError("Error while performing risky operation") from e
    

   


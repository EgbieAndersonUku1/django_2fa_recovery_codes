import logging
from uuid import UUID

from django.utils.timezone import localtime
from datetime import date, datetime

from django_auth_recovery_codes.models import RecoveryCodesBatch
from django_auth_recovery_codes.utils.errors.enforcer import enforce_types


class PurgedStatsCollector:
    """
    Collects and aggregates statistics during recovery code purge operations.

    This helper class tracks the results of purging recovery code batches,
    including how many codes were removed, how many batches were affected,
    and which batches were skipped. It also generates lightweight reports
    for each processed batch. that will be sent to the admin

    Typical usage example:
        collector = PurgeStatsCollector()

        for batch in batches:
            purged_count, is_empty, batch_id = batch.purge_expired_codes()
            collector.process_batch(batch, purged_count, is_empty, batch_id)

        report = collector.batches_report
      
    Attributes:
        total_purged (int): Total number of codes purged across all batches.
        total_batches (int): Total number of batches that had codes purged.
        total_skipped (int): Total number of batches skipped (no codes purged).
        batch_reports (list[dict]): A list of reports, one per processed batch.
        logger: An option logger to log information to a file

   
    """
    def __init__(self, logger: logging.Logger):
        self.total_purged   = 0
        self.total_batches  = 0
        self.batches_report = []
        self.total_skipped  = 0
        self.logger         = logger

        if not isinstance(self.logger, logging.Logger):
            raise TypeError("logger", logging.Logger, logging)
    
    @enforce_types()
    def process_batch(self, 
                      batch: RecoveryCodesBatch, 
                      purged_count: int, 
                      is_empty: bool, 
                      batch_id: UUID,
                      use_with_logger: bool = True):
        """
        Processes a single recovery code batch during a purge operation.

        This method updates internal counters based on whether any codes were purged,
        generates a JSON report for the process batche, and logs information if enabled.

        Args:
            batch (RecoveryCodesBatch): The batch being processed.
            purged_count (int): Number of recovery codes purged from the batch.
            is_empty (bool): Whether the batch was empty after the purge.
            batch_id (str): The unique identifier of the batch.
            use_with_logger (bool, optional): If True, logs purge information. Defaults to True.

        Notes:
            - Type validation is enforced through the `@enforce_types` decorator.
        """

        if purged_count > 0:

            self.total_purged   += purged_count
            self.total_batches  += 1
            self._generate_purged_batch_code_json_report(batch, purged_count, is_empty, batch_id)
            
        else:
            self.total_skipped += 1
        
        self._log_purge_info(purged_count, batch, is_empty, log_information=use_with_logger)


    def _log_purge_info(self, purged_count: int, batch: RecoveryCodesBatch, is_empty: bool, log_information: bool = True):
        """
        Logs information about the purge process for a given recovery code batch.

        Depending on whether any codes were purged, this method logs either an 
        informational or debug message. Logging can be disabled via the 
        `log_information` flag.

        Args:
            purged_count (int): Number of recovery codes purged from the batch.
            batch (RecoveryCodesBatch): The batch being processed.
            is_empty (bool): Whether the batch was empty after the purge.
            log_information (bool, optional): If False, disables logging. Defaults to True.

        Notes:
            - Logs an INFO message when codes are purged.
            - Logs a DEBUG message when no codes are purged (i.e., batch skipped).
            - Intended for internal use within the purge process (leading underscore).
            - Since this method is called from the public `process_batch` method,
                and type checking is already enforced there, parameter validation is
                not repeated here to avoid redundant checks.
        """

        if not log_information:
            return
        
        if purged_count > 0:
            self.logger.info(
                        f"[RecoveryCodes] Batch purged | user_id={batch.user.id}, batch_id={batch.id}, "
                            f"purged_count={purged_count}, is_empty={is_empty}"
                        )
        else:
            self.logger.debug( "[RecoveryCodes] Batch skipped | user_id=%s, batch_id=%s, purged_count=%s",
                                                batch.user.id, batch.id, purged_count
                                            )


    def format_datetime(value):
        """Return a timezone-aware ISO string for datetime, or None."""

        if isinstance(value, datetime):
            return localtime(value).isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return None
    
    def _generate_purged_batch_code_json_report(self, batch: RecoveryCodesBatch, purged_count: int, is_empty: bool, batch_id: UUID) -> dict:
        """
        Creates a JSON report for a purged batch of 2FA recovery codes.

        Each batch contains recovery codes that may be active or expired.
        After purging, this function compiles a structured JSON report with
        details about the batch state and its metadata.

        JSON fields:
            "id": Batch ID.
            "number_issued": Total number of codes issued to the batch.
            "number_removed": Number of codes removed during purge.
            "is_batch_empty": Whether the batch is now empty.
            "number_used": Number of codes already used.
            "number_remaining_in_batch": Active codes still left in the batch.
            "user_issued_to": Username of the person the batch was issued to.
            "batch_creation_date": When the batch was created.
            "last_modified": When the batch was last modified.
            "expiry_date": Expiry date assigned to the batch codes.
            "deleted_at": When the batch was deleted/purged.
            "deleted_by": Who deleted the batch.
            "was_codes_downloaded": Whether codes were downloaded before purge.
            "was_codes_viewed": Whether codes were viewed before purge.
            "was_code_generated": Whether codes were generated before purge.

        Args:
            batch (RecoveryCodesBatch): The purged batch instance.
            purged_count (int): Number of codes deleted during purge.
            is_empty (bool): Whether the batch is now empty after deletion.
            batch_id (str): The batch id for the given batch

        Raises:
            TypeError:
                - If `batch` is not a RecoveryCodesBatch instance.
                - If `purged_count` is not an integer.
                - If `is_empty` is not a boolean.

        Example 1:
            >>> batch = RecoveryCodesBatch.get_by_user(request.user)
            >>> batch.purge_expired_codes()
            >>> report = _generate_purged_batch_code_json_report(batch, purged_count=5, is_empty=True)
            >>> report["number_removed"]
        
        Example Out:
            
            {
                "id": 42,
                "number_issued": 10,
                "number_removed": 8,
                "is_batch_empty": False,
                "number_used": 3,
                "number_remaining_in_batch": 2,
                "user_issued_to": "alice",
                "batch_creation_date": "2025-08-01T09:00:00Z",
                "last_modified": "2025-09-01T12:00:00Z",
                "expiry_date": "2025-09-30T00:00:00Z",
                "deleted_at": "2025-09-01T12:34:56Z",
                "deleted_by": "admin",
                "was_codes_downloaded": True,
                "was_codes_viewed": False,
                "was_code_generated": True,
            }
        """

        purged_batch_info = {
                                "id": str(batch_id),
                                "number_issued": batch.number_issued,
                                "number_removed": purged_count,
                                "is_batch_empty": bool(is_empty),
                                "number_used": batch.number_used,
                                "number_remaining_in_batch": batch.active_codes_remaining,
                                "user_issued_to": getattr(batch.user, "username", None),
                                "batch_creation_date": self.format_datetime(batch.created_at),
                                "last_modified": self.format_datetime(batch.modified_at),
                                "expiry_date": self.format_datetime(batch.expiry_date),
                                "deleted_at": self.format_datetime(batch.deleted_at),
                                "deleted_by": str(batch.deleted_by),
                                "was_codes_downloaded": bool(batch.downloaded),
                                "was_codes_viewed": bool(batch.viewed),
                                "was_codes_emailed": bool(batch.emailed),
                                "was_codes_generated": bool(batch.generated),
                }

        self.batches_report.append(purged_batch_info)
        return purged_batch_info
    
 
 
import logging
import uuid

from django_auth_recovery_codes.models import RecoveryCodesBatch
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg


class PurgedStatsCollector:
    """
    Collects and aggregates statistics during recovery code purge operations.

    This helper class tracks the results of purging recovery code batches,
    including how many codes were removed, how many batches were affected,
    and which batches were skipped. It also generates lightweight reports
    for each processed batch.

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
    def __init__(self, logger):
        self.total_purged   = 0
        self.total_batches  = 0
        self.batches_report = []
        self.total_skipped  = 0
        self.logger         = logger

        if not isinstance(self.logger, logging.Logger):
            raise TypeError("logger", logging.Logger, logging)
       
    def process_batch(self, 
                      batch: RecoveryCodesBatch, 
                      purged_count: int, 
                      is_empty: bool, 
                      batch_id: str,
                      use_with_logger: bool = True):

        self._is_purged_attribrutes_valid(batch, purged_count, is_empty, batch_id)

        if purged_count > 0:

            self.total_purged   += purged_count
            self.total_batches  += 1
            self._generate_purged_batch_code_json_report(batch, purged_count, is_empty, batch_id)
            
        else:
            self.total_skipped += 1
        
        self._log_purge_info(purged_count, batch, is_empty, log_information=use_with_logger)


    def _log_purge_info(self, purged_count, batch, is_empty, log_information = True):

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


    def _generate_purged_batch_code_json_report(self, batch: RecoveryCodesBatch, purged_count: int, is_empty: bool, batch_id: str) -> dict:
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
                                "id": batch_id,
                                "number_issued": batch.number_issued,
                                "number_removed": purged_count,
                                "is_batch_empty": is_empty,
                                "number_used": batch.number_used,
                                "number_remaining_in_batch": batch.active_codes_remaining,
                                "user_issued_to": batch.user.username,
                                "batch_creation_date": batch.created_at,
                                "last_modified": batch.modified_at,
                                "expiry_date": batch.expiry_date,
                                "deleted_at": batch.deleted_at,
                                "deleted_by": batch.deleted_by,
                                "was_codes_downloaded": batch.downloaded,
                                "was_codes_viewed": batch.viewed,
                                "was_codes_email": batch.emailed,
                                "was_code_generated": batch.generated,
                }

        self.batches_report.append(purged_batch_info)
        return purged_batch_info
    
    def _is_purged_attribrutes_valid(self, batch: RecoveryCodesBatch, purged_count: int, is_empty: bool, batch_id: str):
        
        if not isinstance(batch, RecoveryCodesBatch):
            raise TypeError(construct_raised_error_msg("batch", RecoveryCodesBatch, batch))

        if not isinstance(purged_count, int):
            raise TypeError(construct_raised_error_msg("purged_count", int, purged_count))

        if not isinstance(is_empty, bool):
            raise TypeError(construct_raised_error_msg("is_empty", bool, is_empty))

        if not isinstance(batch_id, (str, uuid.UUID)):
            raise TypeError(
               construct_raised_error_msg("batch_id", "str | uuid.UUID", batch_id)
            )
 
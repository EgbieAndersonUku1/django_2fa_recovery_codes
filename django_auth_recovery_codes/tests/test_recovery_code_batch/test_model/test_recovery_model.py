from django.test import TestCase
from django.utils import timezone

from django_auth_recovery_codes.models import RecoveryCodesBatch
from django_auth_recovery_codes.models import Status
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user


class RecoveryCodesBatchModelTest(TestCase):
    """Test suite for RecoveryCodesBatch model."""

    def setUp(self):
        self.user = create_user()
        self.recovery_batch = RecoveryCodesBatch.objects.create(user=self.user)
    
    def test_create_count_one(self):
        """Ensure exactly one RecoveryCodesBatch is created per user."""

        EXPECTED_COUNT_NUM = 1
        qs = RecoveryCodesBatch.objects.filter(user=self.user)
        self.assertTrue(qs.exists())
        self.assertEqual(qs.count(), EXPECTED_COUNT_NUM)
    
    def test_if_has_correct_default_fields(self):
        """Check default field values after creation."""

        EXPECTED_DEFAULT_BATCH_SIZE = 10
        self.recovery_batch.refresh_from_db()

        self.assertEqual(self.recovery_batch.number_issued, EXPECTED_DEFAULT_BATCH_SIZE)
        self.assertEqual(self.recovery_batch.number_removed, 0)
        self.assertEqual(self.recovery_batch.number_invalidated, 0)
        self.assertEqual(self.recovery_batch.number_used, 0)
        self.assertLessEqual(self.recovery_batch.created_at, timezone.now())
        self.assertLessEqual(self.recovery_batch.modified_at, timezone.now())
        self.assertEqual(self.recovery_batch.status, Status.ACTIVE.value)
        self.assertIsNone(self.recovery_batch.expiry_date)
        self.assertIsNone(self.recovery_batch.deleted_at)
        self.assertIsNone(self.recovery_batch.deleted_by)
        self.assertFalse(self.recovery_batch.viewed)
        self.assertFalse(self.recovery_batch.downloaded)
        self.assertFalse(self.recovery_batch.emailed)
        self.assertFalse(self.recovery_batch.generated)
        self.assertTrue(self.recovery_batch.automatic_removal)
        self.assertEqual(self.recovery_batch.requested_attempt, 0)

        self.assertEqual(self.recovery_batch.user, self.user)

    def test_string_representation(self):
        """Ensure string representation includes batch ID and username"""

        EXPECTED_STR = f"Batch {self.recovery_batch.id} for test_user"
        self.assertEqual(str(self.recovery_batch), EXPECTED_STR)
    
    def test_constant_flag(self):
        """Test that all constant flag values and field names are correctly defined."""

        EXPECTED_FLAG_VIEWED_FLAG              = "viewed"
        EXPECTED_FLAG_DOWNLOADED_FLAG          = "downloaded"
        EXPECTED_FLAG_EMAILED_FLAG             = "emailed"
        EXPECTED_FLAG_GENERATED_FLAG           = "generated"
        STATUS_FIELD                           = "status"
        EXPECTED_FLAG_MARK_FOR_DELETION_FIELD  = "mark_for_deletion"
        EXPECTED_FLAG_DELETED_AT_FIELD         = "deleted_at"
        EXPECTED_FLAG_DELETED_BY_FIELD         = "deleted_by"
        EXPECTED_FLAG_REQUEST_ATTEMPT_FIELD    = "requested_attempt"
        EXPECTED_FLAG_NUMBER_USED_FIELD        = "number_used"

        self.assertEqual(self.recovery_batch.VIEWED_FLAG, EXPECTED_FLAG_VIEWED_FLAG)
        self.assertEqual(self.recovery_batch.DOWNLOADED_FLAG, EXPECTED_FLAG_DOWNLOADED_FLAG)
        self.assertEqual(self.recovery_batch.EMAILED_FLAG, EXPECTED_FLAG_EMAILED_FLAG)
        self.assertEqual(self.recovery_batch.GENERATED_FLAG, EXPECTED_FLAG_GENERATED_FLAG)
        self.assertEqual(self.recovery_batch.STATUS_FIELD, STATUS_FIELD)
        self.assertEqual(self.recovery_batch.MARK_FOR_DELETION_FIELD, EXPECTED_FLAG_MARK_FOR_DELETION_FIELD)
        self.assertEqual(self.recovery_batch.DELETED_AT_FIELD, EXPECTED_FLAG_DELETED_AT_FIELD)
        self.assertEqual(self.recovery_batch.DELETED_BY_FIELD, EXPECTED_FLAG_DELETED_BY_FIELD)
        self.assertEqual(self.recovery_batch.REQUEST_ATTEMPT_FIELD, EXPECTED_FLAG_REQUEST_ATTEMPT_FIELD)
        self.assertEqual(self.recovery_batch.NUMBER_USED_FIELD, EXPECTED_FLAG_NUMBER_USED_FIELD)

    def test_cache_key_in_model(self):
        """Test that all constant flag values and field names are correctly defined."""

        EXPECTED_CACHE_KEYS = ["generated", "downloaded", "emailed", "viewed", "number_used"]

        for expected_cache_keys in self.recovery_batch.CACHE_KEYS:
            self.assertIn(expected_cache_keys, EXPECTED_CACHE_KEYS)
    
    def test_json_key_in_model(self):
        """Test that all constant json flag values and field names are correctly defined."""

        EXPECTED_JSON_KEYS = ["id", "number_issued", "number_removed", "number_invalidated", "number_used", "created_at",
                              "modified_at", "expiry_date", "deleted_at", "deleted_by", "viewed", "downloaded",
                              "emailed", "generated", 
                  ]
        for expected_json_keys in self.recovery_batch.JSON_KEYS:
            self.assertIn(expected_json_keys, EXPECTED_JSON_KEYS)

    def test_meta_verbose_name_and_plural(self):
        """Ensure Meta verbose names are correct."""
        self.assertEqual(RecoveryCodesBatch._meta.verbose_name, "RecoveryCodesBatch")
        self.assertEqual(RecoveryCodesBatch._meta.verbose_name_plural, "RecoveryCodeBatches")

    def test_meta_ordering(self):
        """Ensure default ordering is descending by created_at."""
        _ = RecoveryCodesBatch.objects.create(user=self.user)
        batches = list(RecoveryCodesBatch.objects.all())
        self.assertGreaterEqual(batches[0].created_at, batches[-1].created_at)
from django.core.management.base import BaseCommand
from django_q.models import Task, Schedule

class Command(BaseCommand):
    help = "Flush Django Q tasks or scheduler entries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--failed",
            action="store_true",
            help="Flush only failed tasks"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Flush all tasks (failed + successful)"
        )
        parser.add_argument(
            "--scheduler",
            action="store_true",
            help="Flush all scheduled tasks"
        )
        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Do not prompt for confirmation"
        )

    def handle(self, *args, **options):
        if options["all"]:
            target = "all tasks"
        elif options["failed"]:
            target = "failed tasks"
        elif options["scheduler"]:
            target = "scheduler entries"
        else:
            self.stdout.write(self.style.ERROR("No option specified. Use --failed, --all, or --scheduler."))
            return

        if not options.get("noinput"):
            # Confirm with user
            confirm = input(f"Are you sure you want to flush {target}? [yes/no]: ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Flush cancelled."))
                return

        # Perform flush
        if options["all"]:
            count, _ = Task.objects.all().delete()
        elif options["failed"]:
            count, _ = Task.objects.filter(success=False).delete()
        elif options["scheduler"]:
            count, _ = Schedule.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Cleared {count} {target}."))

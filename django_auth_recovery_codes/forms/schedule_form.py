from django import forms
from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler, RecoveryCodeAuditScheduler


class RecoveryCodeCleanUpSchedulerForm(forms.ModelForm):
    
    class Meta:
        model = RecoveryCodeCleanUpScheduler
        fields = "__all__"
        help_texts = {
            "next_run": "Defaults to the calculated schedule time, but you may override it. "
                        "Must not be earlier than Run At.",
        }

    def clean_next_run(self):
        cleaned_data = super().clean()

        run_at   = cleaned_data.get("run_at")
        next_run = cleaned_data.get("next_run")

        if next_run is not None and (run_at > next_run):
            raise forms.ValidationError("The next run cannot be less than run at")
        return next_run
    
    def clean_log_per_code(self):
        """"""
        cleaned_data = super().clean()

        log_per_code = cleaned_data.get("log_per_code")
        bulk_delete  = cleaned_data.get("bulk_delete")

        if log_per_code and bulk_delete:
            raise forms.ValidationError("You cannot set both log_per_code and bulk_delete flag. Only one or the other")
        return log_per_code


    

class RecoveryCodeAuditForm(forms.ModelForm):
    class Meta:
        model = RecoveryCodeAuditScheduler
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if RecoveryCodeAuditScheduler.objects.filter(name=name).exists():
            raise forms.ValidationError("A scheduler with this name already exists. Please choose another.")
        return name


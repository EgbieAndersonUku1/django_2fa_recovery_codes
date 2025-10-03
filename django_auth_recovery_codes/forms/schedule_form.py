from django import forms
from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler, RecoveryCodeAuditScheduler
from django_auth_recovery_codes.base_models import AbstractBaseModel

class RecoveryCodeCleanUpSchedulerForm(forms.ModelForm):
    
    class Meta:
        model = RecoveryCodeCleanUpScheduler
        fields = "__all__"
        help_texts = {
            "next_run": "Defaults to the calculated schedule time, but you may override it. "
                        "Must not be earlier than Run At.",
        }

    def clean_next_run(self):
        """
        Validate that `next_run` is not earlier than `run_at`.
        If `next_run` is None, sets it to the model's default schedule.
        """
        cleaned_data = super().clean()

        run_at   = cleaned_data.get("run_at")
        next_run = cleaned_data.get("next_run")

        if not run_at:
            raise forms.ValidationError("The run at time cannot be None")
        
        if next_run is None:
            next_run = self.instance.next_run_schedule()
        
        if (run_at > next_run):
            raise forms.ValidationError("The next run cannot be less than run at")
        return next_run
    
   

    

class RecoveryCodeAuditForm(forms.ModelForm):
    class Meta:
        model = RecoveryCodeAuditScheduler
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if RecoveryCodeAuditScheduler.objects.filter(name=name).exists():
            raise forms.ValidationError("A scheduler with this name already exists. Please choose another.")
        return name


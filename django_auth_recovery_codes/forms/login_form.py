from django import forms

class LoginForm(forms.Form):
    email  = forms.EmailField(max_length=40, widget=forms.EmailInput(attrs={
        "placeholder": "Add email...",
        "id": "login-email-id",
        "autocomplete": "off",
        "autocapitalize": "none",
    }))
    recovery_code = forms.CharField(
        label="Recovery code",
        max_length=41,
        min_length=41,
        widget=forms.TextInput(
            attrs={
                "placeholder": "987A-CCSSS-9875-125468-14789D",
                "spellcheck": "false",
                "autocorrect": "off",
                "autocomplete": "off",
                "autocapitalize": "none",
                "id": "recovery-code-input",
              
            }
        ),
         initial="",
    )

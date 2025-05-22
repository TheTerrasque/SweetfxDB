from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from django_registration.forms import RegistrationForm as BaseRegistrationForm, User

import requests

# https://www.cloudflare.com/application-services/products/turnstile/

TURNSTILE_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_SECRET = getattr(settings, "CLOUDFLARE_TURNSTILE_SECRET", None)
TURNSTILE_SITEKEY = getattr(settings, "CLOUDFLARE_TURNSTILE_SITEKEY", None)

class CloudflareInput(forms.widgets.Input):
    input_type = "input"
    template_name = "registration/form_field_cloudflare.html"


def validate_turnstile_code(value):
    if not TURNSTILE_SECRET:
        return
    try:
        data = requests.post(TURNSTILE_URL, json={
            "secret": TURNSTILE_SECRET,
            "response": value
        }, timeout=10).json()
        if data["success"]:
            return
        else:
            raise ValidationError("Cloudflare validation fail: %s" % ", ".join(data["error-codes"]))
    except:
        raise ValidationError("Cloudflare error")

class CloudflareRegistrationForm(BaseRegistrationForm):
    turnstile = forms.CharField(
        widget=CloudflareInput(attrs={
            "sitekey": TURNSTILE_SITEKEY
            }), 
        validators=(validate_turnstile_code,), 
        error_messages={'required': 'Cloudflare anti-bot verification failed'},
        label="Antibot verification"
        )

    class Meta(BaseRegistrationForm.Meta):
        fields = [
            User.USERNAME_FIELD,
            User.get_email_field_name(),
            'password1',
            'password2',
            "turnstile"
        ]

RegistrationForm = (TURNSTILE_SECRET and TURNSTILE_SITEKEY) and CloudflareRegistrationForm or BaseRegistrationForm
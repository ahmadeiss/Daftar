from django import forms
from django.contrib.auth import get_user_model

from .models import MerchantProfile


User = get_user_model()


class MerchantProfileCreateForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = MerchantProfile
        fields = (
            "email",
            "password",
            "store_name",
            "owner_name",
            "phone",
            "business_type",
            "plan",
            "city",
            "address",
            "subscription_status",
            "subscription_started_at",
            "subscription_expires_at",
            "notes",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(
            username__iexact=email
        ).exists():
            raise forms.ValidationError("A merchant account with this email already exists.")
        return email


class MerchantProfileChangeForm(forms.ModelForm):
    class Meta:
        model = MerchantProfile
        fields = (
            "user",
            "store_name",
            "owner_name",
            "phone",
            "business_type",
            "plan",
            "city",
            "address",
            "subscription_status",
            "subscription_started_at",
            "subscription_expires_at",
            "notes",
        )

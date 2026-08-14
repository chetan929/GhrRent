from django import forms
from .models import Tenant, Payment


class TenantForm(forms.ModelForm):
    phone = forms.CharField(required=False, max_length=15)

    class Meta:
        model = Tenant
        fields = ["name", "phone", "email", "property", "rent", "pending", "due_day"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["tenant", "amount", "method", "note"]

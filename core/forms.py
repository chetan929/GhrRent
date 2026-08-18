from decimal import Decimal

from django import forms

from .models import MAX_MONEY_VALUE, Tenant, Payment


class TenantForm(forms.ModelForm):
    phone = forms.CharField(required=False, max_length=15)
    rent = forms.DecimalField(
        required=True,
        min_value=Decimal("0.00"),
        max_value=MAX_MONEY_VALUE,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "0.01",
                "max": str(MAX_MONEY_VALUE),
                "inputmode": "decimal",
            }
        ),
    )
    pending = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        max_value=MAX_MONEY_VALUE,
        max_digits=10,
        decimal_places=2,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "0.01",
                "max": str(MAX_MONEY_VALUE),
                "inputmode": "decimal",
            }
        ),
    )
    due_day = forms.IntegerField(min_value=1, max_value=31)

    def clean_rent(self):
        return Tenant.validate_money_value(self.cleaned_data["rent"], "rent")

    def clean_pending(self):
        value = self.cleaned_data.get("pending")
        if value in (None, ""):
            return Decimal("0.00")
        return Tenant.validate_money_value(value, "pending")

    class Meta:
        model = Tenant
        fields = ["name", "phone", "email", "property", "rent", "pending", "due_day"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["tenant", "amount", "method", "note"]

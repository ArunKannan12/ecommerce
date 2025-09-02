from django import forms
from django.core.exceptions import ValidationError
from .models import ProductVariant

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        is_returnable = cleaned_data.get('is_returnable')
        return_days = cleaned_data.get('return_days')
        is_replacement_only = cleaned_data.get('is_replacement_only')
        replacement_days = cleaned_data.get('replacement_days')

        errors = {}

        # Cannot be both
        if is_returnable and is_replacement_only:
            errors['is_returnable'] = ValidationError("Cannot be both returnable and replacement-only.")
            errors['is_replacement_only'] = ValidationError("Cannot be both returnable and replacement-only.")

        # Return days validation
        if is_returnable:
            if not return_days or return_days <= 0:
                errors['return_days'] = ValidationError("Return days must be > 0 if returnable.")
            elif return_days > 30:
                errors['return_days'] = ValidationError("Return days cannot exceed 30.")
        else:
            cleaned_data['return_days'] = None

        # Replacement days validation
        if is_replacement_only:
            if not replacement_days or replacement_days <= 0:
                errors['replacement_days'] = ValidationError("Replacement days must be > 0 if replacement-only.")
            elif replacement_days > 30:
                errors['replacement_days'] = ValidationError("Replacement days cannot exceed 30.")
        else:
            cleaned_data['replacement_days'] = None

        if errors:
            raise ValidationError(errors)

        return cleaned_data

from django import forms
from django.core import validators


class CustomIndexListForm(forms.Form):

    placeholder = 'ATGATTGA (one sequence per line)'

    index_list = forms.CharField(
        label='Enter index sequences',
        required=True,
        widget=forms.Textarea(
            attrs={'placeholder': placeholder, 'rows': 20, }),
    )
    honeypot = forms.CharField(
        label="Leave empty.",
        required=False,
        validators=[validators.MaxLengthValidator(0)],
        widget=forms.HiddenInput,
    )

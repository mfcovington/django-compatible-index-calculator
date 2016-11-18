from django import forms
from django.core import validators

from .models import IndexSet


class AutoIndexListForm(forms.Form):

    index_set_1 = forms.ModelChoiceField(
        queryset=IndexSet.objects.all(),
        required=True,
    )
    subset_size_1 = forms.IntegerField(
        label="Number of indexes to use",
        min_value = 1,
        required=True,
    )

    index_set_2 = forms.ModelChoiceField(
        queryset=IndexSet.objects.all(),
        required=False,
    )
    subset_size_2 = forms.IntegerField(
        label="Number of indexes to use",
        min_value = 1,
        required=False,
    )

    index_set_3 = forms.ModelChoiceField(
        queryset=IndexSet.objects.all(),
        required=False,
    )
    subset_size_3 = forms.IntegerField(
        label="Number of indexes to use",
        min_value = 1,
        required=False,
    )

    samplesheet = forms.FileField(
        label="Upload 'SampleSheet.csv'",
        required=False,
    )


class CustomIndexListForm(forms.Form):

    placeholder = 'ATGATTGA (one sequence per line)'

    index_list = forms.CharField(
        label='Enter index sequences',
        required=False,
        widget=forms.Textarea(
            attrs={'placeholder': placeholder, 'rows': 20, }),
    )
    samplesheet = forms.FileField(
        label="Upload 'SampleSheet.csv'",
        required=False,
    )
    honeypot = forms.CharField(
        label="Leave empty.",
        required=False,
        validators=[validators.MaxLengthValidator(0)],
        widget=forms.HiddenInput,
    )

    def clean(self):
        cleaned_data = super(CustomIndexListForm, self).clean()
        index_list = cleaned_data.get('index_list')
        samplesheet = cleaned_data.get('samplesheet')

        if index_list == '' and samplesheet is None:
            raise forms.ValidationError(
                'Please enter index sequences and/or upload a sample sheet.')


class HiddenSampleSheetDownloadForm(forms.Form):

    filename = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    index_list_csv = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )

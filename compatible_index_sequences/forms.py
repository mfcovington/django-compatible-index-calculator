from django import forms
from django.core import validators

from .models import IndexSet


class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        try:
            rows = kwargs.pop('rows')
        except:
            rows = 20
        placeholder = 'ATGATTGA (one sequence per line)'
        super(BaseForm, self).__init__(*args, **kwargs)
        self.fields['index_list'].widget = forms.Textarea(
            attrs={'placeholder': placeholder, 'rows': rows, })

    config_distance = forms.IntegerField(
        label='Minimum Hamming distance',
        required=True,
    )
    config_length = forms.IntegerField(
        label='Manually set index length (unchecked for auto)',
        required=False,
    )
    index_list = forms.CharField(
        label='Enter index sequences',
        required=False,
    )
    samplesheet_1 = forms.FileField(
        label="Upload 'SampleSheet.csv'",
        required=False,
    )
    samplesheet_2 = forms.FileField(
        label="Upload 'SampleSheet.csv'",
        required=False,
    )
    honeypot = forms.CharField(
        label="Leave empty.",
        required=False,
        validators=[validators.MaxLengthValidator(0)],
        widget=forms.HiddenInput,
    )


class AutoIndexListForm(BaseForm):

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

    extend_search_time = forms.BooleanField(
        label='Extend maximum search time from 10 seconds to 1 minute.<br>'
              '<small>Some searches may take a while to finish, especially '
              'those that involve index sets with different sequence lengths. '
              '<a href="{}">Interactive mode</a> can be useful in such '
              'situations.</small>'.format('/interactive/'),
        required=False,
    )

    def clean(self):
        cleaned_data = super(AutoIndexListForm, self).clean()
        index_set_1 = cleaned_data.get('index_set_1')
        index_set_2 = cleaned_data.get('index_set_2')
        index_set_3 = cleaned_data.get('index_set_3')
        subset_size_1 = cleaned_data.get('subset_size_1')
        subset_size_2 = cleaned_data.get('subset_size_2')
        subset_size_3 = cleaned_data.get('subset_size_3')

        try:
            set_size_1 = len(index_set_1.index_set.all())
            valid_subset_size_1 = (subset_size_1 <= set_size_1)
        except:
            pass
        else:
            if not valid_subset_size_1:
                raise forms.ValidationError(
                    'Number of indexes used ({}) exceeds the number available ({}) for Index set 1 ({}).'.format(
                        subset_size_1, set_size_1, index_set_1))

        if index_set_2 is not None:
            if subset_size_2 is None:
                raise forms.ValidationError(
                    'Please enter number of indexes to use for Index set 2.')

            set_size_2 = len(index_set_2.index_set.all())
            if subset_size_2 > set_size_2:
                raise forms.ValidationError(
                    'Number of indexes used ({}) exceeds the number available ({}) for Index set 2 ({}).'.format(
                        subset_size_2, set_size_2, index_set_2))
        if index_set_3 is not None:
            if subset_size_3 is None:
                raise forms.ValidationError(
                    'Please enter number of indexes to use for Index set 3.')

            set_size_3 = len(index_set_3.index_set.all())
            if subset_size_3 > set_size_3:
                raise forms.ValidationError(
                    'Number of indexes used ({}) exceeds the number available ({}) for Index set 3 ({}).'.format(
                        subset_size_3, set_size_3, index_set_3))

        selected_sets = [s for s in [index_set_1, index_set_2, index_set_3] if s is not None]
        if len(selected_sets) > len(set(selected_sets)):
            raise forms.ValidationError('You selected the same index set multiple times.')


class CustomIndexListForm(BaseForm):

    def clean(self):
        cleaned_data = super(CustomIndexListForm, self).clean()
        config_distance = cleaned_data.get('config_distance')
        config_length = cleaned_data.get('config_length')
        index_list = cleaned_data.get('index_list')
        samplesheet_1 = cleaned_data.get('samplesheet_1')
        samplesheet_2 = cleaned_data.get('samplesheet_2')

        if index_list == '' and samplesheet_1 is None and samplesheet_2 is None:
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

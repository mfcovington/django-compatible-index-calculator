from collections import Counter
import re

from django import forms
from django.core import validators

from .models import IndexSet
from .utils import index_list_from_samplesheet


def clean_custom_index_text(custom_index_text):
    custom_index_list = custom_index_text.splitlines()
    custom_index_list = list(filter(None, custom_index_list))
    custom_index_list = [i.replace(' ', '') for i in custom_index_list]
    return custom_index_list


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


class CompatibilityParameters(forms.Form):

    config_distance = forms.IntegerField(
        initial=3,
        label='Minimum Hamming distance',
        required=True,
    )

    config_length_manual = forms.BooleanField(
        initial=False,
        required=False,
    )
    config_length = forms.IntegerField(
        initial=6,
        label='Manually set index length (unchecked for auto)',
        required=False,
    )

    config_length_manual_2 = forms.BooleanField(
        initial=False,
        required=False,
    )
    config_length_2 = forms.IntegerField(
        initial=6,
        label='Manually set index 2 length (unchecked for auto)',
        required=False,
    )


class AutoIndexListForm(BaseForm, CompatibilityParameters):

    index_set_1 = forms.ModelChoiceField(
        queryset=IndexSet.objects.filter(index_type='i7'),
        required=True,
    )
    subset_size_1 = forms.IntegerField(
        label="Number of indexes to use",
        min_value = 1,
        required=True,
    )

    index_set_2 = forms.ModelChoiceField(
        queryset=IndexSet.objects.filter(index_type='i7'),
        required=False,
    )
    subset_size_2 = forms.IntegerField(
        label="Number of indexes to use",
        min_value = 1,
        required=False,
    )

    index_set_3 = forms.ModelChoiceField(
        queryset=IndexSet.objects.filter(index_type='i7'),
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

        # config_dual = cleaned_data.get('config_dual')
        config_dual = False    # Dual indexing not yet implemented for Auto Mode

        custom_index_list = clean_custom_index_text(
            cleaned_data.get('index_list'))

        try:
            samplesheet_index_set = index_list_from_samplesheet(files=self.files)
        except ValueError as e:
            raise forms.ValidationError(e)

        custom_index_list.extend(samplesheet_index_set.keys())

        if len(custom_index_list) > 0:
            comma_count = Counter()
            for index in custom_index_list:
                comma_count[index.count(',')] += 1
                if re.search('[^acgt,]', index, flags=re.IGNORECASE):
                    raise forms.ValidationError(
                        'Input sequences must be composed of valid bases (e.g., ACGT).')

            dual_detected = False
            if len(comma_count) > 1:
                raise forms.ValidationError(
                    'Input is mix of single-indexing and dual-indexing.')
            elif list(comma_count.keys())[0] == 1:
                dual_detected = True
            elif list(comma_count.keys())[0] != 0:
                raise forms.ValidationError(
                    'Input sequences are neither single-indexed nor dual-indexed.')

            if config_dual != dual_detected:
                raise forms.ValidationError(
                    'Input sequences are inconsistent with choice of {}-indexing.'.format(
                        'dual' if config_dual else 'single'))

            cleaned_data['dual_indexed'] = dual_detected
            cleaned_data['index_list'] = custom_index_list
            cleaned_data['samplesheet_index_set'] = samplesheet_index_set
        return cleaned_data


class CustomIndexListForm(BaseForm, CompatibilityParameters):

    config_dual = forms.BooleanField(
        label='Dual-Indexed?',
        required=False,
        widget=forms.HiddenInput,
    )

    def clean(self):
        cleaned_data = super(CustomIndexListForm, self).clean()
        config_dual = cleaned_data.get('config_dual')
        custom_index_text = cleaned_data.get('index_list')
        samplesheet_1 = cleaned_data.get('samplesheet_1')
        samplesheet_2 = cleaned_data.get('samplesheet_2')

        if (custom_index_text == '' and
                samplesheet_1 is None and
                samplesheet_2 is None):
            raise forms.ValidationError(
                'Please enter index sequences and/or upload a sample sheet.')

        custom_index_list = clean_custom_index_text(custom_index_text)

        try:
            samplesheet_index_set = index_list_from_samplesheet(files=self.files)
        except ValueError as e:
            raise forms.ValidationError(e)

        custom_index_list.extend(samplesheet_index_set.keys())

        comma_count = Counter()
        for index in custom_index_list:
            comma_count[index.count(',')] += 1
            if re.search('[^acgt,]', index, flags=re.IGNORECASE):
                raise forms.ValidationError(
                    'Input sequences must be composed of valid bases (e.g., ACGT).')

        dual_detected = False
        if len(comma_count) > 1:
            raise forms.ValidationError(
                'Input is mix of single-indexing and dual-indexing.')
        elif list(comma_count.keys())[0] == 1:
            dual_detected = True
        elif list(comma_count.keys())[0] != 0:
            raise forms.ValidationError(
                'Input sequences are neither single-indexed nor dual-indexed.')

        if config_dual != dual_detected:
            raise forms.ValidationError(
                'Input sequences are inconsistent with choice of {}-indexing.'.format(
                    'dual' if config_dual else 'single'))

        cleaned_data['dual_indexed'] = dual_detected
        cleaned_data['index_list'] = custom_index_list
        cleaned_data['samplesheet_index_set'] = samplesheet_index_set
        return cleaned_data


class HiddenSampleSheetDownloadForm(forms.Form):

    filename = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    index_list_csv = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    index_list_2_csv = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    sample_ids_csv = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    dual_indexed = forms.BooleanField(
        initial=False,
        widget=forms.HiddenInput,
    )

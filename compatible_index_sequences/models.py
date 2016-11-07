import re

from django.core.validators import RegexValidator
from django.db import models


class IndexSetManager(models.Manager):

    def get_by_natural_key(self, name):
        """For importing data via fixtures without specifying primary key"""
        return self.get(name=name)


class Index(models.Model):

    index_set = models.ForeignKey('IndexSet', on_delete=models.CASCADE)

    name = models.CharField(
        help_text='Enter a brief name for the index sequence.',
        max_length=255,
    )

    sequence = models.CharField(
        help_text='Enter the index sequence.',
        max_length=255,
        validators=[
            RegexValidator(
                regex='^[ACGT]+$',
                message='Not a valid DNA sequence.',
                flags=re.I),
        ],
    )

    class Meta:
        ordering = ['index_set', 'name']
        unique_together = ['index_set', 'name']
        verbose_name = 'Sequencing Index'
        verbose_name_plural = 'Sequencing Indexes'

    def __str__(self):
        return self.name


class IndexSet(models.Model):

    objects = IndexSetManager()

    name = models.CharField(
        help_text='Enter the name of the index sequence set.',
        max_length=255,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        help_text='Enter a description of this index sequence set.',
    )

    url = models.URLField(
        blank=True,
        help_text='Enter a URL associated with this index sequence set.',
    )

    visible_in_interactive = models.BooleanField(
        default=True,
        help_text='Make visible by default in interactive mode.',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Sequencing Index Set'
        verbose_name_plural = 'Sequencing Index Sets'

    def __str__(self):
        return self.name

from django.contrib import admin

from .models import Index, IndexSet


class IndexInline(admin.TabularInline):
    model = Index
    extra = 3


@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    fields = ['name', 'sequence', 'index_set']
    list_display = ['name', 'sequence', 'index_set', 'index_type']
    list_filter = ['index_set', 'index_set__index_type']
    search_fields = ['name', 'sequence', 'index_set__name']


@admin.register(IndexSet)
class IndexSetAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'url', 'index_type', 'visible_in_interactive']
    inlines = [IndexInline]
    list_display = ['name', 'index_type', 'visible_in_interactive', 'url']
    list_filter = ['index_type', 'visible_in_interactive']
    search_fields = ['name', 'description']

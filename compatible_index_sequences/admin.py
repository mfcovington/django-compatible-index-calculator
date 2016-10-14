from django.contrib import admin

from .models import Index, IndexSet


class IndexInline(admin.TabularInline):
    model = Index
    extra = 3


@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    fields = ['name', 'sequence', 'index_set']
    list_display = ['name', 'sequence', 'index_set']
    list_filter = ['index_set']
    search_fields = ['name', 'sequence', 'index_set']


@admin.register(IndexSet)
class IndexSetAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'url']
    inlines = [IndexInline]
    list_display = ['name', 'url']
    search_fields = ['name', 'description']

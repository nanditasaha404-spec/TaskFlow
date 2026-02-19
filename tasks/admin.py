from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'priority', 'due_date', 'completed', 'created_at']
    list_filter = ['completed', 'priority', 'user']
    search_fields = ['title', 'description', 'user__username']
    list_editable = ['completed', 'priority']
    date_hierarchy = 'created_at'
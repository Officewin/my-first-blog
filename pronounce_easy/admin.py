from django.contrib import admin
from .models import PracticeItem


@admin.register(PracticeItem)
class PracticeItemAdmin(admin.ModelAdmin):
    list_display = ["text", "caption"]

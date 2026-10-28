from django.contrib import admin

from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "has_extracted_text", "created_at")
    list_filter = ("status",)
    readonly_fields = ("embedding",)

    @admin.display(boolean=True, description="Has text")
    def has_extracted_text(self, obj):
        return bool(obj.extracted_text)

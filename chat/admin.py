from django.contrib import admin

from .models import Conversation, Message, MessagePhoto


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at")
    inlines = [MessageInline]


@admin.register(MessagePhoto)
class MessagePhotoAdmin(admin.ModelAdmin):
    list_display = ("message", "photo", "rank", "distance")

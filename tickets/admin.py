"""
FiberTrack Tickets - Django Admin
"""
from django.contrib import admin
from .models import (
    TechnicianProfile, Ticket, TicketStatusHistory,
    TicketComment, TicketAttachment
)


class TicketStatusHistoryInline(admin.TabularInline):
    model = TicketStatusHistory
    extra = 0
    readonly_fields = ['previous_status', 'new_status', 'reason', 'changed_by', 'created_at']
    can_delete = False


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 1


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 1


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'skills_list', 'max_workload', 'active_tickets', 'is_available', 'location_updated_at']
    list_filter = ['is_available', 'skills']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def skills_list(self, obj):
        return ', '.join(obj.skills) if obj.skills else '-'
    skills_list.short_description = 'Habilidades'

    def active_tickets(self, obj):
        return obj.active_ticket_count
    active_tickets.short_description = 'Tickets activos'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title', 'priority', 'status', 'assigned_to',
        'ticket_type', 'sla_hours', 'is_overdue', 'created_at'
    ]
    list_filter = ['status', 'priority', 'ticket_type', 'created_at']
    search_fields = ['code', 'title', 'address', 'client__full_name']
    readonly_fields = ['code', 'tracking_token', 'created_at', 'updated_at']
    inlines = [TicketStatusHistoryInline, TicketCommentInline, TicketAttachmentInline]
    date_hierarchy = 'created_at'


@admin.register(TicketStatusHistory)
class TicketStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'previous_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['ticket__code']
    readonly_fields = ['ticket', 'previous_status', 'new_status', 'reason', 'changed_by', 'created_at']


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'visibility', 'created_at']
    list_filter = ['visibility', 'created_at']
    search_fields = ['ticket__code', 'text']


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'attachment_type', 'uploaded_by', 'created_at']
    list_filter = ['attachment_type', 'created_at']
    search_fields = ['ticket__code']

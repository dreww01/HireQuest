from django.contrib import admin
from django.utils.html import format_html, escape
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Source, JobPost, QualificationScore, DraftMessage, AlertStatus


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    list_display = ['identifier', 'type', 'is_active_badge', 'created_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['identifier']
    ordering = ['-created_at']
    actions = ['activate_sources', 'deactivate_sources']
    list_filter_submit = True

    @display(description='Status', label=True)
    def is_active_badge(self, obj):
        return obj.is_active

    @admin.action(description='Activate selected sources')
    def activate_sources(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} source(s) activated successfully.')

    @admin.action(description='Deactivate selected sources')
    def deactivate_sources(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} source(s) deactivated successfully.')


class DraftMessageInline(admin.TabularInline):
    # Inline admin for DraftMessage
    model = DraftMessage
    readonly_fields = ['created_at', 'platform_display', 'content_preview', 'cover_letter_copyable']
    fields = ['platform_display', 'content_preview', 'cover_letter_copyable', 'created_at']
    extra = 0
    can_delete = False

    @display(description='Platform')
    def platform_display(self, obj):
        return obj.get_platform_display()

    @display(description='Message Content (Preview)')
    def content_preview(self, obj):
        preview = obj.content[:200] + '...' if len(obj.content) > 200 else obj.content
        return format_html('<pre style="white-space: pre-wrap; word-wrap: break-word; max-width: 400px;">{}</pre>', escape(preview))

    @display(description='Cover Letter (Click to copy)')
    def cover_letter_copyable(self, obj):
        if not obj.cover_letter:
            return format_html('<em>No cover letter</em>')

        safe_id = f'cover_letter_{obj.id}'
        copy_btn = f'<button type="button" onclick="copyToClipboard(\'{safe_id}\')" style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">Copy</button>'

        return format_html(
            '<div style="display: flex; align-items: flex-start;">'
            '<pre id="{}" style="white-space: pre-wrap; word-wrap: break-word; max-width: 400px; margin: 0; flex: 1;">{}</pre>'
            '{}'
            '</div>',
            safe_id,
            escape(obj.cover_letter[:300] + '...' if len(obj.cover_letter) > 300 else obj.cover_letter),
            copy_btn
        )


@admin.register(JobPost)
class JobPostAdmin(ModelAdmin):
    list_display = ['title', 'source', 'status_badge', 'author', 'timestamp']
    list_filter = ['status', 'source__type', 'created_at']
    search_fields = ['title', 'body', 'author', 'external_id']
    ordering = ['-timestamp']
    readonly_fields = ['external_id', 'created_at', 'updated_at', 'job_description_preview', 'apply_link', 'application_link_display', 'cover_letter_section']
    fields = ['title', 'source', 'author', 'status', 'external_id', 'timestamp', 'url', 'application_link', 'application_link_display', 'apply_link', 'job_description_preview', 'cover_letter_section', 'created_at', 'updated_at']
    actions = ['mark_as_closed', 'mark_as_sent']
    list_filter_submit = True
    list_fullwidth = True
    inlines = [DraftMessageInline]

    @display(description='Status', label=True)
    def status_badge(self, obj):
        return obj.status

    @display(description='Job Description')
    def job_description_preview(self, obj):
        preview = obj.body[:500] + '...' if len(obj.body) > 500 else obj.body
        return format_html(
            '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; max-width: 600px;">'
            '<pre style="white-space: pre-wrap; word-wrap: break-word; margin: 0; font-size: 12px;">{}</pre>'
            '</div>',
            escape(preview)
        )

    @display(description='Source Link (Reddit/Email)')
    def apply_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank" style="padding: 8px 12px; background-color: #417690; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">'
            'Open Source Link'
            '</a>',
            escape(obj.url)
        )

    @display(description='Application Link (LinkedIn/Glassdoor/etc.)')
    def application_link_display(self, obj):
        if not obj.application_link:
            return format_html('<em style="color: #999;">No application link found</em>')
        return format_html(
            '<a href="{}" target="_blank" style="padding: 8px 12px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">'
            '✓ Apply to This Job'
            '</a>',
            escape(obj.application_link)
        )

    @display(description='Cover Letter')
    def cover_letter_section(self, obj):
        try:
            draft = obj.draft
            if not draft or not draft.cover_letter:
                return format_html('<em style="color: #999;">No cover letter generated</em>')

            safe_id = f'job_cover_letter_{obj.id}'
            copy_btn = '<button type="button" onclick="copyToClipboard(\'{}\');" style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">Copy All</button>'.format(safe_id)

            return format_html(
                '<div>'
                '<div style="display: flex; align-items: flex-start; margin-bottom: 10px;">'
                '<pre id="{}" style="white-space: pre-wrap; word-wrap: break-word; max-width: 600px; margin: 0; flex: 1; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>'
                '{}'
                '</div>'
                '<small style="color: #666;">Source: Draft Message (Platform: {})</small>'
                '</div>',
                safe_id,
                escape(draft.cover_letter),
                copy_btn,
                escape(draft.get_platform_display())
            )
        except DraftMessage.DoesNotExist:
            return format_html('<em style="color: #999;">No draft message available</em>')

    @admin.action(description='Mark selected jobs as closed')
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} job(s) marked as closed.')

    @admin.action(description='Mark selected jobs as sent')
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status='sent')
        self.message_user(request, f'{updated} job(s) marked as sent.')


@admin.register(QualificationScore)
class QualificationScoreAdmin(ModelAdmin):
    list_display = ['job_post', 'classification_badge', 'confidence', 'is_job_signal_badge', 'created_at']
    list_filter = ['classification', 'is_job_signal', 'created_at']
    search_fields = ['job_post__title', 'reasoning']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    list_filter_submit = True

    @display(description='Classification', label=True)
    def classification_badge(self, obj):
        return obj.classification

    @display(description='Job Signal', label=True)
    def is_job_signal_badge(self, obj):
        return obj.is_job_signal


@admin.register(DraftMessage)
class DraftMessageAdmin(ModelAdmin):
    list_display = ['job_post', 'platform_badge', 'has_cover_letter_badge', 'created_at']
    list_filter = ['platform', 'created_at']
    search_fields = ['job_post__title', 'content', 'cover_letter']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'content_display', 'cover_letter_display']
    fields = ['job_post', 'platform', 'content_display', 'cover_letter_display', 'created_at']
    list_filter_submit = True

    @display(description='Platform', label=True)
    def platform_badge(self, obj):
        return obj.platform

    @display(description='Cover Letter', label=True)
    def has_cover_letter_badge(self, obj):
        return bool(obj.cover_letter)

    @display(description='Message Content')
    def content_display(self, obj):
        return format_html(
            '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; max-width: 600px;">'
            '<pre style="white-space: pre-wrap; word-wrap: break-word; margin: 0; font-size: 12px;">{}</pre>'
            '</div>',
            escape(obj.content)
        )

    @display(description='Cover Letter (Copyable)')
    def cover_letter_display(self, obj):
        if not obj.cover_letter:
            return format_html('<em style="color: #999;">No cover letter</em>')

        safe_id = f'draft_cover_letter_{obj.id}'
        copy_btn = '<button type="button" onclick="copyToClipboard(\'{}\');" style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">Copy</button>'.format(safe_id)

        return format_html(
            '<div style="display: flex; align-items: flex-start;">'
            '<pre id="{}" style="white-space: pre-wrap; word-wrap: break-word; max-width: 600px; margin: 0; flex: 1; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>'
            '{}'
            '</div>',
            safe_id,
            escape(obj.cover_letter),
            copy_btn
        )


@admin.register(AlertStatus)
class AlertStatusAdmin(ModelAdmin):
    list_display = ['job_post', 'acknowledged_badge', 'sent_at', 'telegram_message_id']
    list_filter = ['acknowledged', 'sent_at']
    search_fields = ['job_post__title', 'telegram_message_id']
    ordering = ['-sent_at']
    readonly_fields = ['sent_at']
    actions = ['mark_as_acknowledged']
    list_filter_submit = True

    @display(description='Acknowledged', label=True)
    def acknowledged_badge(self, obj):
        return obj.acknowledged

    @admin.action(description='Mark as acknowledged')
    def mark_as_acknowledged(self, request, queryset):
        updated = queryset.update(acknowledged=True)
        self.message_user(request, f'{updated} alert(s) marked as acknowledged.')

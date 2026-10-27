# crm/models/activity.py
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from tenancy.models import TenantBaseModel

class Activity(TenantBaseModel):
    class ActivityType(models.TextChoices):
        CALL = 'CALL', 'Phone Call'
        EMAIL = 'EMAIL', 'Email sent/received'
        MEETING = 'MEETING', 'Meeting'
        TASK = 'TASK', 'Task/Todo'
        NOTE = 'NOTE', 'Internal Note'
        SYSTEM = 'SYSTEM', 'System Log/Audit'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, related_name='crm_activities',
        null=True,
        blank=True
    )

    activity_type = models.CharField(max_length=7, choices=ActivityType.choices, default=ActivityType.NOTE)
    subject = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    meta_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Activities"
        ordering = ['-created_at']
        indexes = [
            # Fast lookups for timelines on specific records
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.activity_type} - {self.subject}"
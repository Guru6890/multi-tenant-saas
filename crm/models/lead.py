# crm/models/lead.py
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

from tenancy.models import TenantBaseModel
from identity.models import User

class Lead(TenantBaseModel):
    class LeadType(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        BUSINESS = 'BUSINESS', 'Business'

    class ContactMethod(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        PHONE = 'PHONE', 'Phone'
        WHATSAPP = 'WHATSAPP', 'Whatsapp'
        SMS = 'SMS', 'SMS'

    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        ATTEMPTED_CONTACT = 'ATTEMPTED_CONTACT', 'Attempted Contact'
        CONTACTED = 'CONTACTED', 'Contacted'
        QUALIFIED = 'QUALIFIED', 'Qualified'
        UNQUALIFIED = 'UNQUALIFIED', 'Unqualified'
        CONVERTED = 'CONVERTED', 'Converted'

    class Source(models.TextChoices):
        WEBSITE = 'WEBSITE', 'Website'
        INBOUND_CALL = 'INBOUND_CALL', 'Inbound Call'
        REFERRAL = 'REFERRAL', 'Referral'
        CAMPAIGN = 'CAMPAIGN', 'Campaign'
        WALK_IN = 'WALK_IN', 'Walk In'
        OUTBOUND = 'OUTBOUND', 'Outbound'

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    type = models.CharField(max_length=10, choices=LeadType.choices, db_index=True)
    display_name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    phone = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[\d\s\-\(\)]{7,20}$",
                message="Enter a valid phone number."
            )
        ]
    )
    preferred_contact_method = models.CharField(max_length=8, choices=ContactMethod.choices, default=ContactMethod.EMAIL)
    status = models.CharField(max_length=18, choices=Status.choices, default=Status.NEW)
    source = models.CharField(max_length=13, choices=Source.choices)
    address = models.TextField(null=True, blank=True)
    assigned_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='leads_assigned')
    notes = models.TextField(null=True, blank=True)

    converted_at = models.DateTimeField(null=True, blank=True)
    converted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='converted_leads')

    qualification_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
        )
    

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.display_name} ({self.get_status_display()})"
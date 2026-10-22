# crm/models/pipeline.py
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from decimal import Decimal

from tenancy.models import TenantBaseModel
from crm.models.customer import Customer

class Pipeline(TenantBaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    is_default = models.BooleanField(default=False, help_text='Only one default pipeline is recommended per workspace.')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'name'],
                name='unique_pipeline_name_per_workspace'
            ),
            models.UniqueConstraint(
                fields=['workspace'],
                condition=models.Q(is_default=True),
                name='unique_default_pipeline_per_workspace'
            )
        ]

    def __str__(self):
        return self.name
    
class PipelineStage(TenantBaseModel):
    class StageType(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        WON = 'WON', 'Won'
        LOST ='LOST', 'Lost'

    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(help_text='Visual ordering priority e.x (1, 2, 3)')
    probability = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=10,
        help_text='Win probability percentage (0-100)'
    )
    stage_type = models.CharField(max_length=4, choices=StageType.choices, default=StageType.OPEN, db_index=True)
    is_closed = models.BooleanField(default=False, editable=False)
    is_won = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ['pipeline', 'order']
        constraints = [
            models.UniqueConstraint(
                fields = ['workspace', 'pipeline', 'name'],
                name = 'unique_name_for_pipeline'
            ),
            models.UniqueConstraint(
                fields=["workspace", "pipeline", "order"],
                name="unique_stage_order_per_pipeline",
            ),
        ]

    def __str__(self) -> str:
        return f'{self.pipeline.name} -> {self.name}'
    
    def clean(self):
        super().clean()
        if self.stage_type == self.StageType.WON:
            self.is_closed = True
            self.is_won = True
            self.probability = 100
        elif self.stage_type == self.StageType.LOST:
            self.is_closed = True
            self.is_won = False
            self.probability = 0
        else:
            self.is_closed = False
            self.is_won = False

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Deal(TenantBaseModel):
    class Status(models.TextChoices):  # kept only as constants for the service layer
        OPEN = 'OPEN', 'Open'
        WON = 'WON', 'Won'
        LOST = 'LOST', 'Lost'

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='deals')
    stage = models.ForeignKey(PipelineStage, on_delete=models.PROTECT, related_name='deals')
    title = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_deals',
        null=True,
        blank=True
    )

    won_at = models.DateTimeField(null=True, blank=True)
    lost_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'stage']),
            models.Index(fields=['workspace', 'assigned_to']),
            models.Index(fields=['expected_close_date']),
        ]

    def __str__(self):
        return f"{self.title} (${self.value})"

    @property
    def pipeline(self):
        return self.stage.pipeline if self.stage_id else None
    
    @property
    def status(self) -> str:
        if not self.stage_id:
            return self.Status.OPEN
        return (
            {
                PipelineStage.StageType.WON.value: self.Status.WON,
                PipelineStage.StageType.LOST.value: self.Status.LOST,
            }.get(self.stage.stage_type, self.Status.OPEN)
        )
    
    @property
    def weighted_value(self) -> Decimal:
        """Expected revenue = value × stage probability."""
        if self.status != self.Status.OPEN:
            return self.value if self.status == self.Status.WON else Decimal("0.00")
        return (self.value * Decimal(self.stage.probability) / Decimal("100")).quantize(
            Decimal("0.01")
        )

    @property
    def is_overdue(self) -> bool:
        if self.status != self.Status.OPEN or not self.expected_close_date:
            return False
        return self.expected_close_date < timezone.now().date()
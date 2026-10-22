import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal

from tenancy.models import TenantBaseModel
from inventory.catalogue.models import Product
from inventory.catalogue.models import UnitOfMeasure
from crm.models.pipeline import Deal

class Quote(TenantBaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CONVERTED_TO_ORDER = 'CONVERTED_TO_ORDER', 'Converted to order'

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.PROTECT, related_name='quotes')
    quote_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    valid_until = models.DateField(blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'quote_number'],
                name='unique_quote_number_per_workspace'
            )
        ]

    def __str__(self):
        return f"{self.quote_number} ({self.get_status_display()})"
    
class QuoteItem(TenantBaseModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='quote_items')
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='quote_items')
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal("0.001"))]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]   
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]    
    )
    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]    
    )
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.product} x {self.quantity}'
    
    def calculate_totals(self):
        gross = self.unit_price * self.quantity
        discount = gross * (self.discount_percent / Decimal('100'))
        line_subtotal = (gross - discount).quantize(Decimal('0.01'))
        self.tax_amount = (line_subtotal * (self.tax_percent / Decimal('100'))).quantize(Decimal('0.01'))
        self.total_price = line_subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        self.calculate_totals()
        self.full_clean()
        super().save(*args, **kwargs)
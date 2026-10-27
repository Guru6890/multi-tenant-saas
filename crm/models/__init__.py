# crm/models/__init__.py

from .activity import Activity
from .business_profile import BusinessProfile
from .contact import Contact
from .customer import Customer, Address
from .lead import Lead
from .pipeline import Pipeline, PipelineStage, Deal
from .quote import Quote, QuoteItem

__all__ = [
    'Activity',
    'BusinessProfile',
    'Contact',
    'Customer',
    'Address',
    'Lead',
    'Pipeline',
    'PipelineStage',
    'Deal',
    'Quote',
    'QuoteItem'
]
# crm/services/lead_conversion_service.py
from typing import Optional, Dict, Any, Tuple
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from crm.models.customer import Customer, Address
from crm.models.contact import Contact
from crm.models.lead import Lead
from crm.services.address_service import AddressService
from crm.services.contact_service import ContactService
from crm.services.customer_service import CustomerService
from crm.selectors.customer_selectors import customer_exists_by_email
from crm.exceptions import CustomerAlreadyExistsError

from authorization.services import AuthorizationService
from identity.models import User

LEAD_CONVERT = 'crm.lead.convert'

class LeadConversionService:
    @staticmethod
    @transaction.atomic
    def convert_lead(
        *,
        user: User,
        workspace,
        lead: Lead,
        contact_data: Optional[Dict[str, Any]] = None,
        address_data: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Tuple[Customer, Optional[Contact], Optional[Address]]:
        AuthorizationService.require_permission(user, workspace, LEAD_CONVERT)

        if lead.status == Lead.Status.CONVERTED:
            raise ValidationError('This lead has already been converted.')
        if customer_exists_by_email(lead.email):
            raise CustomerAlreadyExistsError(
                f"Cannot convert lead: A customer with email '{lead.email}' already exists in this workspace."
            )
        
        customer_notes = notes or lead.notes
        customer = CustomerService.create(
            user=user,
            workspace=workspace,
            display_name=lead.display_name,
            customer_type=lead.type,
            email=lead.email,
            phone=lead.phone,
            notes=customer_notes
        )

        primary_contact: Optional[Contact] = None
        if contact_data:
            primary_contact = ContactService.create(
                user=user,
                workspace=workspace,
                customer=customer,
                name=contact_data.get('name', lead.display_name),
                job_title=contact_data.get('job_title', 'Primary Contact'),
                email=contact_data.get('email', lead.email),
                phone=contact_data.get('phone', lead.phone),
                is_primary=True,
                is_active=True,
            )

        primary_address: Optional[Address] = None
        if address_data:
            primary_address = AddressService.create(
                user=user,
                workspace=workspace,
                customer=customer,
                purpose=address_data.get('purpose', Address.Purpose.BILLING),
                line1=address_data['line1'],
                line2=address_data.get('line2', ''),
                city=address_data['city'],
                state=address_data['state'],
                postal_code=address_data['postal_code'],
                country=address_data['country'],
                label=address_data.get('label', 'Primary Address'),
                is_primary=True,
                is_active=True
            )

        lead.status = Lead.Status.CONVERTED
        lead.converted_at = timezone.now()
        lead.converted_by = user
        lead.save(update_fields=['status', 'converted_at', 'converted_by'])

        return (customer, primary_contact, primary_address)
# crm/selectors/lead_selectors.py
from typing import Optional, Any
from django.db.models import QuerySet, Q
from crm.models.lead import Lead


def get_lead_queryset(*, workspace: Any) -> QuerySet[Lead]:
    """
    Base selector providing a tenant-isolated QuerySet for leads.
    """
    return Lead.objects.filter(workspace=workspace)


def get_lead_by_id(*, workspace: Any, lead_id: str) -> Optional[Lead]:
    """
    Fetches a single lead by ID within a workspace context.
    """
    return get_lead_queryset(workspace=workspace).filter(id=lead_id).first()


def lead_exists_by_email(*, workspace: Any, email: str) -> bool:
    """
    Checks if an active (non-converted) lead exists for the given email in the workspace.
    """
    return (
        get_lead_queryset(workspace=workspace)
        .filter(email__iexact=email)
        .exclude(status=Lead.Status.CONVERTED)
        .exists()
    )


def list_leads(
    *,
    workspace: Any,
    status: Optional[str] = None,
    source: Optional[str] = None,
    lead_type: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    search_query: Optional[str] = None,
    min_score: Optional[int] = None,
) -> QuerySet[Lead]:
    """
    Lists and filters leads with support for status, source, score, and text search.
    """
    qs = get_lead_queryset(workspace=workspace)

    if status:
        qs = qs.filter(status=status)

    if source:
        qs = qs.filter(source=source)

    if lead_type:
        qs = qs.filter(type=lead_type)

    if assigned_to_user_id:
        qs = qs.filter(assigned_to_user_id=assigned_to_user_id)

    if min_score is not None:
        qs = qs.filter(qualification_score__gte=min_score)

    if search_query:
        qs = qs.filter(
            Q(display_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    return qs
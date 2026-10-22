# crm/exceptions.py
class CRMException(Exception):
    """Base exception for CRM domain logic errors."""
    pass

class CustomerAlreadyExistsError(CRMException):
    """Raised when a customer with the same email exists in the workspace."""
    pass

class InvalidCustomerStatusTransitionError(CRMException):
    """Raised when attempting an illegal customer status transition."""
    pass

class CustomerTypeMismatchError(CRMException):
    """Raised when individual/business profile constraints are violated."""
    pass
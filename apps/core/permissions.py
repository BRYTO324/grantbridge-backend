"""Custom permission classes for role-based access control."""
from rest_framework.permissions import BasePermission, IsAuthenticated


class IsEntrepreneur(BasePermission):
    """Allow access only to authenticated users with role=entrepreneur."""

    message = "Only entrepreneurs can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "entrepreneur"
        )


class IsFunder(BasePermission):
    """Allow access only to authenticated users with role=funder."""

    message = "Only funders can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "funder"
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the owner of an object can edit/delete it.
    Assumes the model has an `entrepreneur` or `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        from rest_framework.permissions import SAFE_METHODS

        if request.method in SAFE_METHODS:
            return True

        # Support both .entrepreneur and .user owner fields
        owner = getattr(obj, "entrepreneur", None) or getattr(obj, "user", None)
        return owner == request.user


class IsVerified(BasePermission):
    """Allow access only to users whose verification_status is 'verified'."""

    message = "Your account must be verified to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.verification_status == "verified"
        )

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Anyone can view artisans.

    Only the owner can edit or delete an artisan.
    """

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and obj.owner == request.user
        )
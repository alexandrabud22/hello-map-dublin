from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission for artisan locations.

    - Anyone (including anonymous visitors) can read.
    - Only the user who created the artisan can edit or delete it.
    - Staff users (administrators) can moderate any artisan.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and (obj.owner == user or user.is_staff)
        )


class IsStaffOrReadOnly(BasePermission):
    """
    Used for cultural regions and heritage routes.

    These are curated reference layers, so anyone can read them,
    but only staff users can create, update or delete them.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return bool(user and user.is_authenticated and user.is_staff)

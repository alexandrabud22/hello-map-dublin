from rest_framework.permissions import BasePermission, SAFE_METHODS

# Anyone can read; only the owner or staff can change a workshop.
class IsOwnerOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and (obj.owner == user or user.is_staff)
        )

# Only staff can change the shared regions and routes.
class IsStaffOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return bool(user and user.is_authenticated and user.is_staff)

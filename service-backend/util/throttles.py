# project_root/service-backend/util/throttles.py
from rest_framework.throttling import UserRateThrottle

class StaffUserRateThrottle(UserRateThrottle):
    """
    Custom throttle to exempt staff and superusers from rate limiting.
    """
    def allow_request(self, request, view):
        """
        Return `True` if the request is from a staff or superuser, `False` otherwise.
        """
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        return super().allow_request(request, view)

"""
Auth URLs - login, logout, profile, MFA verification stub.
"""
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Return current user's role and tenant."""
    from apps.partners.models import SystemUser
    try:
        su = SystemUser.objects.get(user=request.user)
        return Response({
            'user_id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'role': su.role,
            'sub_center_id': str(su.sub_center_id) if su.sub_center_id else None,
            'sub_center_code': su.sub_center.center_code if su.sub_center else None,
        })
    except SystemUser.DoesNotExist:
        return Response({
            'user_id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'role': 'super_admin' if request.user.is_superuser else None,
            'sub_center_id': None,
            'sub_center_code': None,
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_mfa(request):
    """
    Stub for MFA OTP verification.

    Production: integrates with Keycloak Authentication Flow
    (OTP-over-WhatsApp primary, SMS fallback). For dev/tests, accepts
    any 6-digit code.
    """
    otp = request.data.get('otp', '')
    if len(str(otp)) == 6 and str(otp).isdigit():
        return Response({'status': 'verified', 'method': 'dev-stub'})
    return Response({'detail': 'Invalid OTP'}, status=400)


urlpatterns = [
    path('token', obtain_auth_token, name='token-auth'),
    path('profile', profile, name='profile'),
    path('mfa/verify', verify_mfa, name='verify-mfa'),
]

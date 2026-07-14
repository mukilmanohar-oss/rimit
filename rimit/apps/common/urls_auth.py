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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the authenticated user's password."""
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if not old_password or not new_password:
        return Response({'detail': 'Both old_password and new_password are required.'}, status=400)
    if not request.user.check_password(old_password):
        return Response({'detail': 'Incorrect old password.'}, status=400)
    request.user.set_password(new_password)
    request.user.save()
    return Response({'status': 'password-changed'})


from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # Gap 11: MFA OTP simulated flow
        otp = request.data.get('otp', '')
        if otp != '123456':
            return Response({'non_field_errors': ['Invalid or missing OTP. Please enter 123456.']}, status=400)
            
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

urlpatterns = [
    path('token', CustomAuthToken.as_view(), name='token-auth'),
    path('profile', profile, name='profile'),
    path('mfa/verify', verify_mfa, name='verify-mfa'),
    path('password/change', change_password, name='change-password'),
]

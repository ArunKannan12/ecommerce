# Create your views here.
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import status, generics
from rest_framework.response import Response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import CustomUser,ActivationEmailLog,PasswordResetEmailLog
from .serializers import (ResendActivationEmailSerializer,
                            CustomPasswordResetSerializer,
                            CustomPasswordResetConfirmSerializer,
                            FacebookLoginSerializer,
                            CustomerProfileSerializer,
                            PromoterProfileSerializer,
                            InvestorProfileSerializer,
                            BaseUserSerializer,
                            DeliveryManProfileSerializer
                            )
from rest_framework.parsers import MultiPartParser, FormParser
from cloudinary.uploader import upload, destroy
from django.middleware.csrf import get_token
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
import math
from djoser.utils import encode_uid
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth import get_user_model
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.exceptions import TokenError
import requests
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.email import CustomActivationEmail
from rest_framework_simplejwt.views import TokenRefreshView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

User = get_user_model()

secure=settings.DEBUG is False


class ResendActivationEmailView(generics.GenericAPIView):
    serializer_class = ResendActivationEmailSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_address = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email_address)
        except CustomUser.DoesNotExist:
            return Response(
                {'email': 'User with this email does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_permanently_banned:
            return Response(
                {'detail': 'Your account has been permanently banned due to repeated abuse.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.is_active and user.is_verified:
            return Response(
                {'detail': 'User is already activated and verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        now = timezone.now()

        if user.blocked_until and now < user.blocked_until:
            remaining = int((user.blocked_until - now).total_seconds())
            return Response(
                {'detail': f'Too many resend attempts. Please try again after {remaining} seconds.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        one_hour_ago = now - timedelta(hours=1)
        recent_logs = ActivationEmailLog.objects.filter(user=user, sent_at__gte=one_hour_ago)

        if recent_logs.count() >= 5:
            user.block_count += 1

            # Progressive block durations: 15 min, 1 hour, 24 hours
            block_durations = [
                timedelta(minutes=15),
                timedelta(hours=1),
                timedelta(days=1),
            ]

            if user.block_count <= len(block_durations):
                user.blocked_until = now + block_durations[user.block_count - 1]
            else:
                # Permanent ban after exceeding blocks
                user.is_permanently_banned = True
                user.blocked_until = None
                user.save(update_fields=['block_count', 'blocked_until', 'is_permanently_banned'])
                return Response(
                    {'detail': 'Your account has been permanently banned due to repeated abuse.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            user.save(update_fields=['block_count', 'blocked_until'])
            block_time = user.blocked_until - now
            minutes = int(block_time.total_seconds() / 60)
            return Response(
                {'detail': f'Too many resend attempts. Your account has been temporarily disabled for {minutes} minutes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Exponential cooldown logic
        base_cooldown = 10  # seconds
        exponential_factor = min(recent_logs.count(), 4)
        cooldown_duration = timedelta(seconds=base_cooldown * (2 ** exponential_factor))

        if user.last_activation_email_sent and now - user.last_activation_email_sent < cooldown_duration:
            remaining = cooldown_duration - (now - user.last_activation_email_sent)
            return Response(
                {'detail': f'Activation email was sent recently. Please try again after {int(remaining.total_seconds())} seconds.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Send activation email
        token = default_token_generator.make_token(user)
        context = {
            "user": user,
            "uid": encode_uid(user.pk),
            "token": token,
            "site": get_current_site(request),
            "activation_url": f"{settings.FRONTEND_URL.rstrip('/')}/activation/{encode_uid(user.pk)}/{token}/",
        }

        activation_email = CustomActivationEmail(
            request,
            context=context,
            user=user,
        )
        activation_email.send(to=[user.email])
       
        user.last_activation_email_sent = now
        user.save(update_fields=['last_activation_email_sent'])

        ActivationEmailLog.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        return Response({'detail': 'Activation email resent.'}, status=status.HTTP_200_OK)

    
class CustomPasswordResetView(generics.GenericAPIView):
    serializer_class = CustomPasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'email': 'User with this email does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.auth_provider.lower() != 'email':
            return Response(
                {'detail': f"Password reset is not allowed for users signed up with {user.auth_provider.title()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()

        if user.blocked_until_password_reset and now < user.blocked_until_password_reset:
            seconds_left = int((user.blocked_until_password_reset - now).total_seconds())
            minutes_left = math.ceil(seconds_left / 60)
            return Response(
                {'detail': f'Too many password reset attempts. Try again after {minutes_left} minutes.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        base_cooldown = 60
        max_attempts = 5
        cooldown_time = timedelta(seconds=base_cooldown * (2 ** user.block_count_password_reset))

        if user.last_password_reset_sent and (now - user.last_password_reset_sent) < cooldown_time:
            seconds_left = int((cooldown_time - (now - user.last_password_reset_sent)).total_seconds())
            minutes_left = math.ceil(seconds_left / 60)
            return Response(
                {'detail': f'Please wait {minutes_left} minutes before requesting another password reset.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if user.block_count_password_reset >= max_attempts:
            user.blocked_until_password_reset = now + timedelta(minutes=15)
            user.block_count_password_reset = 0
            user.save(update_fields=['blocked_until_password_reset', 'block_count_password_reset'])
            return Response(
                {'detail': 'Too many attempts. Please try again after 15 minutes.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer.save()

        # Update user tracking fields
        user.last_password_reset_sent = now
        user.block_count_password_reset += 1
        user.save(update_fields=['last_password_reset_sent', 'block_count_password_reset'])

        # Log the password reset attempt
        PasswordResetEmailLog.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        return Response({"detail": "Password reset email sent successfully."}, status=status.HTTP_200_OK)


class CustomPasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = CustomPasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)

class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token_str = request.data.get('id_token')

        if not id_token_str:
            return Response({'error': 'ID Token is required'}, status=400)

        try:
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )

            email = idinfo.get('email')
            first_name = idinfo.get('given_name', 'Google')
            last_name = idinfo.get('family_name', '')
            picture_url = idinfo.get('picture')

            if not email:
                return Response({'error': 'Invalid ID Token (email not found)'}, status=400)

            try:
                user = User.objects.get(email=email)
                if user.auth_provider.lower() != 'google':
                    return Response({
                        'error': f"This email is already registered using {user.auth_provider.capitalize()} login. Please use that method instead.",
                        'auth_provider': user.auth_provider
                    }, status=400)
                created = False  # Since we fetched the existing user
            except User.DoesNotExist:
                user = User.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_verified=True,
                    is_active=True,
                    auth_provider='google',
                    social_auth_pro_pic=picture_url
                )
                created = True

            # Update profile picture if changed
            if picture_url and user.social_auth_pro_pic != picture_url:
                user.social_auth_pro_pic = picture_url
                user.save(update_fields=['social_auth_pro_pic'])

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            response =  Response({

                'email': user.email,
                'full_name': user.get_full_name(),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role':user.role,
                'social_auth_pro_pic': user.social_auth_pro_pic,
                'auth_provider': user.auth_provider,
                'is_new_user': created,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'message': 'Google authentication successful'
            }, status=status.HTTP_200_OK)

            access_token = str(refresh.access_token)
            refresh_token = str(refresh)


            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure = not settings.DEBUG,
                samesite='Lax',
                max_age=3600
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure = not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60

            )
            # Capture IP address
            ip = (
                request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR")
            )
            if ip:
                user.last_login_ip = ip
                user.save(update_fields=["last_login_ip"])

            return response

           
        

        except ValueError:
            return Response({'error': 'Invalid ID Token (verification failed)'}, status=status.HTTP_400_BAD_REQUEST)


User=get_user_model()
class FacebookLoginView(GenericAPIView):
    serializer_class = FacebookLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data.get('access_token')

        # Step 1: Get basic Facebook user data
        fb_response = requests.get(
            'https://graph.facebook.com/me',
            params={
                'fields': 'id,name,email',
                'access_token': access_token
            }
        )
        if fb_response.status_code != 200:
            return Response({'error': 'Invalid Facebook token'}, status=status.HTTP_400_BAD_REQUEST)

        fb_data = fb_response.json()
        email = fb_data.get('email')
        name = fb_data.get('name', '')
        user_id = fb_data.get('id')

        if not email:
            return Response({'error': 'Facebook account must provide an email'}, status=status.HTTP_400_BAD_REQUEST)

        first_name = name.split(' ')[0]
        last_name = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''

        # Step 2: Fetch profile picture
        pic_response = requests.get(
            f"https://graph.facebook.com/v19.0/{user_id}/picture",
            params={
                "access_token": access_token,
                "redirect": False,
                "type": "large",
            }
        )
        social_auth_pro_pic = None
        if pic_response.status_code == 200:
            social_auth_pro_pic = pic_response.json().get("data", {}).get("url")


        try:
            user = User.objects.get(email=email)
            if user.auth_provider.lower() != 'facebook':
                return Response({
                    'error': f"This email is already registered using {user.auth_provider.capitalize()} login. Please use that method instead.",
                    'auth_provider': user.auth_provider
                }, status=status.HTTP_400_BAD_REQUEST)
            created = False
            # Optional: Update profile info
            user.first_name = first_name
            user.last_name = last_name
            if social_auth_pro_pic:
                user.social_auth_pro_pic = social_auth_pro_pic
            user.save()
        except User.DoesNotExist:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                
                is_verified=True,
                is_active=True,
                auth_provider='facebook',
                social_auth_pro_pic=social_auth_pro_pic
            )
            created = True

        # Step 4: Generate tokens
        refresh = RefreshToken.for_user(user)

        response =  Response({
            'email': user.email,
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role':user.role,
            'auth_provider': 'facebook',
            'is_new_user': created,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'profile_picture': user.social_auth_pro_pic,
            'message': 'Facebook authentication successful'
        }, status=status.HTTP_200_OK)

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)


        response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure = not settings.DEBUG,
                samesite='Lax',
                max_age=3600
            )
        response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure = not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60,
                path='/'

            )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'No refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            new_refresh_token = str(token)
            token.blacklist()

            response = Response({'message': 'Token refreshed'}, status=status.HTTP_200_OK)

            response.set_cookie('access_token', new_access_token, httponly=True, secure=not settings.DEBUG,
                                samesite='Lax', path='/', max_age=60 * 60)
            response.set_cookie('refresh_token', new_refresh_token, httponly=True, secure=not settings.DEBUG,
                                samesite='Lax', path='/', max_age=7 * 24 * 60 * 60)

            # Refresh CSRF token
            csrf_token = get_token(request)
            response.set_cookie('csrftoken', csrf_token, httponly=False, secure=not settings.DEBUG,
                                samesite='Lax', path='/', max_age=60 * 60)

            return response

        except TokenError:
            return Response({'error': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code != 200:
            return response  # Login failed

        refresh = response.data.get('refresh')
        access = response.data.get('access')
        email = request.data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_verified:
            return Response({'error': 'User is not verified'}, status=status.HTTP_403_FORBIDDEN)

        remember_me = request.data.get('remember_me', False)
        res = Response({
            'message': 'Login successful',
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name
        }, status=status.HTTP_200_OK)

        # Set access token cookie
        res.set_cookie('access_token', access, httponly=True, secure=not settings.DEBUG,
                   samesite='Lax', path='/', max_age=60 * 60)
        res.set_cookie('refresh_token', refresh, httponly=True, secure=not settings.DEBUG,
                    samesite='Lax', path='/', max_age=7 * 24 * 60 * 60 if remember_me else None)

        # 🔐 Set CSRF token cookie
        csrf_token = get_token(request)
        res.set_cookie('csrftoken', csrf_token, httponly=False, secure=not settings.DEBUG,
                    samesite='Lax', path='/', max_age=60 * 60)

        return res

    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Optional: log invalid token

        response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        response.delete_cookie('csrftoken',path='/')
        return response
    

@method_decorator(ensure_csrf_cookie, name='dispatch')
class SetCSRFCookieView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})
    
from django.http import JsonResponse

def custom_jwt_view(request):
    access_token = request.COOKIES.get('access_token')
    refresh_token = request.COOKIES.get('refresh_token')
    
    print("Access token:", access_token)
    print("Refresh token:", refresh_token)
    
    return JsonResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    role_serializers = {
        "customer": CustomerProfileSerializer,
        "promoter": PromoterProfileSerializer,
        "investor": InvestorProfileSerializer,
        "deliveryman": DeliveryManProfileSerializer,
        "admin": BaseUserSerializer,
        "warehouse": BaseUserSerializer,
    }

    allowed_update_roles = ["customer", "promoter", "investor", "deliveryman"]

    def get_serializer(self, user, *args, **kwargs):
        serializer_class = self.role_serializers.get(user.role, BaseUserSerializer)
        return serializer_class(user, *args, **kwargs)

    def get(self, request):
        user = request.user
        if not user.is_active:
            return Response({"detail": "Your account is inactive."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(user, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        return self.update(request, partial=False)

    def patch(self, request):
        return self.update(request, partial=True)

    def delete(self, request):
        user = request.user
        if user.custom_user_profile:
            try:
                destroy(f"custom_user_profile_pics/{user.id}_profile", resource_type="image")
            except Exception:
                pass
        user.delete()
        return Response({"detail": "Your profile has been deleted."}, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, partial):
        user = request.user

        # Profile pic delete
        if str(request.data.get("delete_profile_pic", "")).lower() == "true" and user.custom_user_profile:
            try:
                destroy(f"custom_user_profile_pics/{user.id}_profile", resource_type="image")
                user.custom_user_profile = None
                user.save()
            except Exception:
                return Response({"detail": "Image deletion failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Profile pic upload
        image_file = request.FILES.get("custom_user_profile")
        if image_file:
            print(f"Received file: {image_file.name}, content_type: {image_file.content_type}, size: {image_file.size}")
            if not image_file.content_type.startswith("image/"):
                return Response({"detail": "Invalid file type. Only images are allowed."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                result = upload(
                    image_file,
                    folder="custom_user_profile_pics",
                    public_id=f"{user.id}_profile",
                    overwrite=True,
                    resource_type="image",
                    transformation={"width": 300, "height": 300, "crop": "fill"},
                )
                print(f"Cloudinary upload result: {result}")
                user.custom_user_profile = result.get("secure_url")
                user.save()
            except Exception as e:
                print("Image upload exception:", e)
                return Response({"detail": "Image upload failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not user.is_active:
            return Response({"detail": "Your account is inactive."}, status=status.HTTP_403_FORBIDDEN)

        if user.role not in self.allowed_update_roles:
            return Response({"detail": "You are not allowed to update your profile."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(user, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import os

@csrf_exempt
def create_temp_superuser(request):
    secret = request.GET.get('key')
    if secret != os.getenv("SUPERUSER_SECRET_KEY"):
        return HttpResponse("Unauthorized", status=401)

    User = get_user_model()
    email = os.getenv("TEMP_SUPERUSER_EMAIL")
    password = os.getenv("TEMP_SUPERUSER_PASSWORD")
    first_name = os.getenv("TEMP_SUPERUSER_FIRST_NAME", "Admin")
    last_name = os.getenv("TEMP_SUPERUSER_LAST_NAME", "User")

    if User.objects.filter(email=email).exists():
        return HttpResponse("Superuser already exists")

    User.objects.create_superuser(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        is_verified=True,
        role="admin"
    )
    return HttpResponse("Superuser created successfully")

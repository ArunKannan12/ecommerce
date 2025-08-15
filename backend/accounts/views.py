# Create your views here.
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import status, generics
from rest_framework.response import Response
from django.conf import settings
from .models import CustomUser,ActivationEmailLog,PasswordResetEmailLog
from .serializers import (ResendActivationEmailSerializer,
                            CustomPasswordResetSerializer,
                            CustomPasswordResetConfirmSerializer,
                            FacebookLoginSerializer,
                            
                            )
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
                secure=secure,
                samesite='Lax',
                max_age=3600
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=secure,
                samesite='Lax',
                max_age=7*24*60*60

            )

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
                secure=secure,
                samesite='Lax',
                max_age=3600
            )
        response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=secure,
                samesite='Lax',
                max_age=7*24*60*60

            )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'No refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Validate and rotate the token
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)

            # If rotating, generate a new refresh token
            if True:  # Optional: check your settings
                new_refresh_token = str(token)
                token.blacklist()  # Blacklist old one if setting is enabled

            # Create response and set new tokens
            response = Response({'message': 'Token refreshed'}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=new_access_token,
                httponly=True,
                secure=False,  # False for development
                samesite='Lax',
                max_age=60 * 60
            )
            response.set_cookie(
                key='refresh_token',
                value=new_refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60
            )
            return response

        except TokenError:
            return Response({'error': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            refresh = response.data.get('refresh')
            access = response.data.get('access')

            # Return only a success message (tokens go in cookies)
            user = CustomUser.objects.get(email=request.data.get('email'))
            if not user.is_verified:
                return Response({'error':'user in not verified'},status=status.HTTP_403_FORBIDDEN)
            res = Response({
                'message': 'Login successful'
                ,'access': access,
                'refresh': refresh,
                'email':user.email,
                'role':user.role,

                'first_name': user.first_name,
                'last_name': user.last_name
                },
                  status=status.HTTP_200_OK)
            

            res.set_cookie(
                key='access_token',
                value=access,
                httponly=True,
                secure=False,  # Use False during local dev
                samesite='Lax',
                max_age=60 * 60  # 1 hour
            )
            res.set_cookie(
                key='refresh_token',
                value=refresh,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            return res

        # Return original response if login fails (e.g. 401)
        return response
    
class LogoutView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()  # <-- This line
        except Exception:
            pass  # Optional: log invalid or missing token

        response = Response({'message': 'Logged out successfully'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
    

@method_decorator(ensure_csrf_cookie, name='dispatch')
class SetCSRFCookieView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})
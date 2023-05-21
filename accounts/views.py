import os
from urllib import response

#directory import
from config.views import ResponseCode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

#rest_framework packages
from rest_framework import generics, permissions, status, views
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

#serializers
from .serializers import (
    ForgetPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserSerializer,
)

User = get_user_model()
class CustomRedirect(HttpResponsePermanentRedirect):

    allowed_schemes = [os.environ.get("APP_SCHEME"), "http", "https"]


class RegisterView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():       
            user = serializer.save(is_active=False)
            uid =urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                'Your default token',
                'Activate your account with this link www.google.com/token={}/{}'.format(uid,token),
                'your_email@example.com',
                [user.email],
                fail_silently=False,
            )
            user_data = serializer.data
            response = ResponseCode.success(message="Your account has been created",data=user_data)

        return Response(response, status=status.HTTP_201_CREATED)



class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        
        # Get the user from the validated serializer data
        user = serializer.validated_data['user']
        # Get the token from the validated serializer data
        token = serializer.validated_data['access']
        refresh_token = serializer.validated_data['refresh']

        response_data = {
            'access_token': token,
            'refresh_token': refresh_token,
            'user_id': user.id,
            'name': user.first_name,
            'email': user.email
            
            }
        response = ResponseCode.success(message="User Authentication Successful", data = response_data)
        return Response(response, status=status.HTTP_200_OK)

class ActivateUser(APIView):    
    permission_class = (AllowAny,)

    def get(self,request,uidb64,token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                response = ResponseCode.success(message="Your Account Has been Activated",data={""})
                return Response(response, status=status.HTTP_200_OK)
            else:
                response =ResponseCode.error(message="The token you have entered is invalid",data={""})
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            response =ResponseCode.error(message="The token you have entered is invalid",data={""})
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class GetUserDetail(ModelViewSet):
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    http_method_names = ["get","put","delete"]

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            response_code = {
            "code":"3000",
            "status":"400",
            "message":"User Not Found",
            "data":"Unauthorized User"
        }
            response = ResponseCode.error(message="User not found",data=response_code)
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)

    def list(self,request,*args, **kwargs):
        user = self.request.query_params.get("user_id")
        if user:
            user = get_object_or_404(User,id=user,is_active=True)
            serializer = self.get_serializer(user,context={"request":request})
            response = ResponseCode.success(message="User Profile Details", data=serializer.data)
            return Response(response, status=status.HTTP_200_OK)

        user = str(request.user.id)
        user_data = get_object_or_404(User,id=user, is_active=True)
        serializer = self.get_serializer(user_data,context={"request":request})
        response = ResponseCode.success(message="User Profile Detail",data=serializer.data)
        return Response(response,status=status.HTTP_200_OK)

    def update(self,request,*args,**kwargs):
        user = request.user.id
        instance = self.get_object()
        user_id = int(kwargs.get("pk"))
        if user_id != user:
            response = "You don't have permission to update this profile"
            return Response(response,status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(instance=instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_code = message="Profile has been updated"
        return Response(response_code,status=status.HTTP_201_CREATED)

    def delete(self,request,*args,**kwargs):
        user = request.user.id
        user = User.objects.get(id=request.user.id).delete()
        response = ResponseCode.success(message="User Account Deleted Successfully",data={""})
        return Response(response,status=status.HTTP_200_OK)



class ForgotPassword(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgetPasswordSerializer

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            response_code = {
            "code":"3000",
            "status":"400",
            "message":"User Not Found",
            "data":"Unauthorized User"
        }
            return Response(response_code, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)


    def post(self,request,*args, **kwargs):
        email = request.data.get("email")
        user = get_object_or_404(User,email=email,is_active=True)
        if user:
            uid =urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                'Your default token',
                'Activate your account with this link www.google.com/token={}/{}'.format(uid,token),
                'your_email@example.com',
                [user.email],
                fail_silently=False,
            )
        response_code = "Success a link has ben sent to you confirm your email"
        return Response(response_code,status=status.HTTP_200_OK)




class LogoutView(APIView):
    def post(self, request):
        refresh_token = None
        
        # Extract the refresh token from the request headers
        authorization_header = request.headers.get('Authorization')
        if authorization_header and authorization_header.startswith('Bearer '):
            refresh_token = authorization_header.split(' ')[1]
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                response = ResponseCode.success(message="Logout successful",data={"success":"logout successful"})
                return Response(response, status=status.HTTP_200_OK)
            except Exception:
                return Response({'detail': 'Invalid refresh token.'}, status=400)
        else:
            return Response({'detail': 'Refresh token is required.'}, status=400)

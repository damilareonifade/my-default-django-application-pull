from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=200,required=True)
    last_name= serializers.CharField(required=True)
    role = serializers.CharField(required=True)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model = User
        exclude = ("is_superuser","is_staff","updated_at","created_at","user_permissions","groups")

    def create(self, validated_data):
        password = validated_data.pop("password",None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance



class LoginSerializer(TokenObtainPairSerializer):

    def get_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def validate(self, attrs):
        data = super().validate(attrs)
        email = attrs.get("email")
        user = self.get_user(email)

        
        if not user or not user.is_active:
            raise serializers.ValidationError("User account is not active.")
        refresh = self.get_token(user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add user data to the validated serializer data
        data["user"] = self.user
        data['user_id'] = self.user.id
        data['first_name'] = self.user.first_name

        data['email'] = self.user.email

        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_message = {"bad_token": ("Token is expired or invalid")}

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):

        try:
            RefreshToken(self.token).blacklist()

        except TokenError:
            self.fail("bad_token")


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=250,write_only=True,required=True)
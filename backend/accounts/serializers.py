from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "name", "password")
        read_only_fields = ("id",)
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": False, "allow_blank": True},
        }

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def create(self, validated_data):
        password = validated_data.pop("password")
        name = validated_data.pop("name", "").strip()
        email = validated_data["email"]
        username = validated_data.get("username") or email

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name,
            )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": "An account with this email already exists."}
            ) from exc
        return user


class EmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs.get("email") or attrs.get("username")
        password = attrs.get("password")
        if not login:
            raise serializers.ValidationError({"email": "Email is required."})

        user_lookup = (
            User.objects.filter(email__iexact=login).first()
            or User.objects.filter(username__iexact=login).first()
        )
        username = user_lookup.get_username() if user_lookup else login
        user = authenticate(
            request=self.context.get("request"),
            username=username,
            password=password,
        )

        if user is None or not user.is_active:
            raise serializers.ValidationError("Unable to log in with provided credentials.")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }

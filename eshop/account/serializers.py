from rest_framework import serializers
from django.contrib.auth.models import User


# signup serializer
class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True , 'allow_blank': False},
            'password': {'required': True, 'allow_blank': False, 'allow_null': False, 'min_length': 6}
        }

# user serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
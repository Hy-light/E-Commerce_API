from rest_framework.decorators import api_view, permission_classes

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from datetime import timedelta, datetime

from .serializers import SignUpSerializer, UserSerializer
from utils.helpers import get_current_host
 
#  Views
@api_view(['POST'])
def register(request):
    data = request.data
    
    user = SignUpSerializer(data=data)
    
    if user.is_valid():
        if not User.objects.filter(username=data['email']).exists():
            
            user = User.objects.create(
                first_name = data['first_name'],
                last_name = data['last_name'],
                email = data['email'],
                username = data['email'],
                password = make_password(data['password'])
            )
            
            return Response({'success': 'User created successfully'}, status=status.HTTP_201_CREATED)
        
        else:
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = UserSerializer(request.user, many=False)
    return Response(user.data)

# Update user
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user
    data = request.data
    
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.email = data['email']
    user.username = data['email']
    
    if data['password'] != "":
        user.password = make_password(data['password'])
        
    user.save()
    
    updated_user = UserSerializer(user, many=False)
    
    return Response(updated_user.data)


# Reset password
@api_view(['POST'])
def forgot_password(request):
    data = request.data 
    
    user = get_object_or_404(User, email=data['email'])
    
    token = get_random_string(length=40)
    expire_date = datetime.now() + timedelta(minutes=30)
    
    user.profile.reset_password_token = token
    user.profile.reset_password_expire = expire_date
    
    user.profile.save()
    host = get_current_host(request)
    
    # Send email with token
    link = f'{host}api/reset_password/{token}'.format(host=host, token=token)
    body = "Your password reset link is: {link}".format(link=link)
    
    send_mail(
        'Password reset for eshop',
        body,
        'noreply@eshop.com',
        [data['email']]
    )
    
    return Response({'success': 'Email sent with password reset link sent to {email}'.format(email=data)}, status=status.HTTP_200_OK)



# Reset password
@api_view(['POST'])
def reset_password(request, token):
    data = request.data
    
    user = get_object_or_404(User, profile__reset_password_token=token)
    
    if user.profile.reset_password_expire.replace(tzinfo=None) < datetime.now():
        return Response({'error': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    if data['password'] != data['confirm_password']:
        return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.password = make_password(data['password'])
    user.profile.reset_password_token = ''
    user.profile.reset_password_expire = None
    
    user.profile.save()
    user.save()
    
    return Response({'success': 'Password reset successfully'}, status=status.HTTP_200_OK)
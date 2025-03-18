from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
import os 

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Order, OrderItem
from .serializers import OrderSerializer
from product.models import Product 
from .filters import OrderFilter

import stripe 
from utils.helpers import get_current_host



# Post new order
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_order(request):
    
    user = request.user
    data = request.data
    
    order_items = data['orderItems']
    
    if order_items and len(order_items) == 0:
        return Response({'error': 'No Order Items. Please add atleast one product'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Create order
        
        total_amount = sum([item['price'] * item['quantity'] for item in order_items])
        
        order = Order.objects.create(
            user=user,
            street = data['street'],
            state = data['state'],
            city = data['city'],
            zip_code = data['zip_code'],
            country = data['country'],
            phone_no = data['phone_no'],
            total_amount=total_amount
        )
        
        # Create order items
        for i in order_items:
            product = Product.objects.get(id=i['product'])
            
            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                quantity=i['quantity'],
                price=i['price']
            )
            
            # Update stock
            product.stock -= item.quantity
            product.save()
        
        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


# Get all orders
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):
    
    filterset = OrderFilter(request.GET, queryset=Order.objects.all().order_by('id'))
    count = filterset.qs.count()
    
    # pagination
    resPerPage = 2
    
    paginator = PageNumberPagination()
    paginator.page_size = resPerPage
    
    queryset = paginator.paginate_queryset(filterset.qs, request)
    
    # orders = Order.objects.all()
    serializer = OrderSerializer(queryset, many=True)
    return Response({'count': count, 'resPerPage': resPerPage, 'order': serializer.data}, status=status.HTTP_200_OK)


# Get order by pk
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    
    order = get_object_or_404(Order, id=pk)
    serializer = OrderSerializer(order, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def process_order(request, pk):
    
    order = get_object_or_404(Order, id=pk)
    
    order.status = request.data['status']
    order.save()

    serializer = OrderSerializer(order, many=False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_order(request, pk):
    
    order = get_object_or_404(Order, id=pk)
    order.delete()
    
    return Response({'message': 'Order deleted'}, status=status.HTTP_200_OK)


stripe.api_key = os.environ.get('STRIPE_PRIVATE_KEY')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    
    YOUR_DOMAIN = get_current_host(request)
    
    user = request.user
    data = request.data
    
    order_items = data['orderItems']
    
    shipping_details = {
        'street': data['street'],
        'state': data['state'],
        'city': data['city'],
        'zip_code': data['zip_code'],
        'country': data['country'],
        'phone_no': data['phone_no'],
        'user' : user.id
    }
    
    checkout_order_items = []
    for i in order_items:
        checkout_order_items.append({
            'price_data': {
                'currency': 'gbp',
                'product_data': {
                    'name': i['name'],
                    'images': [i['image']],
                    'metadata': {
                        'product_id': i['product'],
                    },  
                },
                'unit_amount': int(i['price'] * 100)
            },
            'quantity': i['quantity'],
        })
        
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        metadata= shipping_details,
        line_items=checkout_order_items,
        customer_email=user.email,
        mode='payment',
        success_url=YOUR_DOMAIN, # + '/payment/success/',
        cancel_url=YOUR_DOMAIN #+ '/payment/cancel/',
    )
    
    return Response({'session': session}, status=status.HTTP_200_OK)

# webhook request
@api_view(['POST'])
def  stripe_webhook(request):
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return Response({'error' : 'Invalid Payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return Response({'error' : 'Invalid Signature'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # print('session', session)
        line_items = stripe.checkout.Session.list_line_items(session['id'])
        
        price = session['amount_total'] / 100
        
        order = Order.objects.create(
            user = User(session.metadata.user),
            street = session.metadata.street,
            state = session.metadata.state,
            city = session.metadata.city,
            zip_code = session.metadata.zip_code,
            country = session.metadata.country,
            phone_no = session.metadata.phone_no,
            total_amount = price,
            payment_status = "PAID",
            payment_mode = "Card"
        )
        
        for item in line_items['data']:
            
            line_product = stripe.Product.retrieve(item.price.product)
            product_id = line_product.metadata.product_id
            
            product = Product.objects.get(id=product_id)
            
            order_item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                quantity=item.quantity,
                price=item.price.unit_amount / 100,
                image = line_product.images[0]
            )
            
            product.stock -= item.quantity
            product.save()
        
        
        return Response({'details': 'Payment successful'}, status=status.HTTP_200_OK)
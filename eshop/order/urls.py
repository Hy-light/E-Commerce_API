from django.urls import path
from . import views

urlpatterns = [
    path('orders/new/', views.new_order, name='order_new'),   
    path('orders/', views.get_orders, name='get_orders'),
    path('orders/<str:pk>/', views.get_order, name='get_order'),
    path('orders/<str:pk>/process/', views.process_order, name='process_order'),
    path('orders/<str:pk>/delete/', views.delete_order, name='delete_order'),
    
    path('create_checkout_session/', views.create_checkout_session, name='create_checkout_session'),
    path('order/webhook/', views.stripe_webhook, name='stripe_webhook'),
]
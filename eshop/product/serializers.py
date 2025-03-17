from rest_framework import serializers
from .models import *


class ReviewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Review
        fields = '__all__'
        

class ProductImageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductImages
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField(method_name='get_reviews', read_only=True)
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'description', 'brand', 'ratings', 'reviews', 'category','stock', 'user', 'images')
        
        extra_kwargs = {
            "name": {"required": True, 'allow_blank': False},
            "description": {"required": True, 'allow_blank': False},
            "brand": {"required": True, 'allow_blank': False},
            "category": {"required": True, 'allow_blank': False},
        }
        
    def get_reviews(self, obj):
        reviews = obj.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

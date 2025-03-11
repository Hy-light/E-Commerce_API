# Django imports
from django.shortcuts import get_object_or_404

# Django-REST-Framework imports
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

# 
from .models import Product, ProductImages
from .filters import ProductsFilter
from .serializers import ProductSerializer, ProductImageSerializer

# Create your views here.

# get all products
@api_view(['GET'])
def get_products(request):
    # Filtering products using Django-Filter
    filterset = ProductsFilter(request.GET, queryset=Product.objects.all().order_by('id'))
    
    count = filterset.qs.count()
    
    # pagination 
    resPerPage = 2
    
    paginator = PageNumberPagination()
    paginator.page_size = resPerPage
    
    queryset = paginator.paginate_queryset(filterset.qs, request)
    
    # Serializing the filtered products using Django-REST-Framework serializer
    serializer = ProductSerializer(queryset, many=True)
    return Response({
        'count': count,
        'resPerPage': resPerPage,
        'products': serializer.data
        })

# get product details
@api_view(['GET'])
def get_product(request, pk):

    product = get_object_or_404(Product, id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response({'product': serializer.data})
    
    
# upload image files
@api_view(['POST'])
def upload_product_images(request):
    
    data = request.data
    files = request.FILES.getlist('images')

    images = []
    for file in files:
        image = ProductImages.objects.create(product=Product(data['product']), image=file)
        images.append(image)
        
    serializer = ProductImageSerializer(images, many=True)
    
    return Response(serializer.data)
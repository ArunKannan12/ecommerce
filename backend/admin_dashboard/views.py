from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdmin
from .serializers import AdminDashboardStatsSerializer,ProductAdminSerializer
from products.models import Product,ProductVariant
from rest_framework.generics import ListAPIView,CreateAPIView,UpdateAPIView,RetrieveAPIView,RetrieveUpdateDestroyAPIView

class AdminDashboardStatsAPIView(APIView):
    permission_classes=[IsAuthenticated,IsAdmin]

    def get(self,request):
        serializer=AdminDashboardStatsSerializer({})
        return Response(serializer.data)
    

class ProductAdminCreateAPIView(CreateAPIView):
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        return Product.objects.all()
       
      
    
class ProductAdminDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class=ProductAdminSerializer
    permission_classes=[IsAdmin]
    lookup_field='id'

    def get_queryset(self):
        return Product.objects.all()


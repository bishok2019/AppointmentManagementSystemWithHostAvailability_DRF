from .permission_serializers import PermissionCategoryCreateSerializer, PermissionCategoryListSerializer, PermissionCategoryDetailSerializer, PermissionCategoryUpdateSerializer
from .models import PermissionCategory
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSuperUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .permissions import HasPermission, IsSuperUser
from custom_pagination import CustomPageNumberPagination

# class PermissionCategoryListCreateView(generics.ListCreateAPIView):
#     queryset = PermissionCategory.objects.all()
#     filterset_fields = ['is_active']
#     search_fields = ['name']

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return PermissionCategoryCreateSerializer
#         return PermissionCategoryListSerializer

# class PermissionCategoryDetailView(generics.RetrieveUpdateAPIView):
#     queryset = PermissionCategory.objects.all()
    # serializer_class = PermissionCategoryDetailSerializer

class CreatePermissionCategoryView(APIView):
    serializer_class = PermissionCategoryCreateSerializer
    permission_classes=[IsSuperUser]
    # required_permission = 'can_create_permission_cat'
    def post(self, request):
        serializer = PermissionCategoryCreateSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            permission = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Permission Category created successfully.',
                'data': PermissionCategoryDetailSerializer(permission).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetPermissionCategoryView(APIView):
    serializer_class = PermissionCategoryListSerializer
    permission_classes=[IsSuperUser|HasPermission]
    required_permission = 'can_read_permission_cat'
    pagination_class = CustomPageNumberPagination

    def get(self, request):
        permission = PermissionCategory.objects.all()
        if permission.exists():
            serializer = PermissionCategoryDetailSerializer(permission, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"msg": "Permission Category Not Found."}, status=status.HTTP_404_NOT_FOUND)

class UpdatePermissionCategoryView(APIView):
    serializer_class = PermissionCategoryUpdateSerializer
    permission_classes=[IsSuperUser]
    # required_permission = 'can_update_permission_cat'
    # serializer_class = PermissionCategoryDetailSerializer
    def get(self, request, pk=None):
        if pk is not None:
            permission = PermissionCategory.objects.filter(pk=pk)
            if permission:
                serializer = PermissionCategoryDetailSerializer(permission, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"msg": "Permission Category Not Found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk=None, format=None):
        permission_to_update = PermissionCategory.objects.filter(pk=pk).first()
        if not permission_to_update:
            return Response({"msg": "Permission Category Not Found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PermissionCategoryUpdateSerializer(permission_to_update, data=request.data, context={'request':request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Permission Category successfully updated!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
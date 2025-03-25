from .models import Role
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
from .permissions import IsSuperUser
# from user.pagination import CustomPagination
# from django_filters.rest_framework import DjangoFilterBackend
from .role_serializers import RoleCreateSerializer, RoleListSerializer, RoleDetailSerializer, RoleUpdateSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .permissions import HasPermission
from custom_pagination import CustomPageNumberPagination
from rest_framework.generics import ListAPIView

class CreateRoleView(APIView):
    permission_classes=[HasPermission]
    required_permission = 'can_create_role'
    serializer_class = RoleCreateSerializer
    def post(self, request):
        serializer = RoleCreateSerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            role = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Role created successfully.',
                'data': RoleCreateSerializer(role).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# class GetRoleView(APIView):
#     serializer_class = RoleListSerializer
#     permission_classes=[HasPermission]
#     required_permission = 'can_read_role'
#     pagination_class = CustomPageNumberPagination
#     def get(self, request, pk=None):
#         role = Role.objects.all()
#         if role.exists():
#             serializer = RoleListSerializer(role, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response({"msg": "No Role found."}, status=status.HTTP_404_NOT_FOUND)
class GetRoleView(ListAPIView):
    permission_classes=[HasPermission]
    required_permission = 'can_read_role'
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleDetailSerializer
    pagination_class = CustomPageNumberPagination

class UpdateRoleView(APIView):
    serializer_class = RoleUpdateSerializer
    permission_classes=[HasPermission]
    required_permission = 'can_update_role'

    def get(self, request, pk=None):
        if pk is not None:
            role = Role.objects.filter(pk=pk)
            if role.exists():
                serializer = RoleDetailSerializer(role, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"msg": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk=None, format=None):
        role_to_update = Role.objects.filter(pk=pk).first()
        if not role_to_update:
            return Response({"msg": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleUpdateSerializer(role_to_update, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Role successfully updated!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
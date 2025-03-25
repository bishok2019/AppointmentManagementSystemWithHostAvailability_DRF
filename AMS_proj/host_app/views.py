from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Department
from role_app.models import Role
from .permissions import HasRolePermission
from custom_pagination import CustomPageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout

class DepartmentRegistrationView(APIView):
    # permission_classes = [HasRolePermission]
    # required_permission = 'can_create_department'
    serializer_class = DepartmentSerializer
    
    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            department = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Department created successfully.',
                'data': DepartmentSerializer(department).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GetDepartmentView(ListAPIView):
    # permission_classes = [HasRolePermission]
    # required_permission = 'can_read_department'
    queryset=Department.objects.all().order_by('id')
    serializer_class = DepartmentSerializer
    pagination_class = CustomPageNumberPagination

class UpdateDepartmentView(APIView):
    # permission_classes = [HasRolePermission]
    # required_permission = 'can_update_department'
    serializer_class = DepartmentSerializer

    def get(self, request, pk=None):
        if pk is not None:
            department = Department.objects.filter(pk=pk)
            if department.exists():
                serializer = DepartmentSerializer(department, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"msg": "Department not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk=None, format=None):
        department_to_update = Department.objects.filter(pk=pk).first()
        if not department_to_update:
            return Response({"msg": "Department not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DepartmentSerializer(department_to_update, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Department successfully updated!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserRegistrationView(APIView):
    # permission_classes = [HasRolePermission]
    # required_permission = 'can_create_user'
    serializer_class = UserSerializer
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if 'role' not in request.data:
                default_role = Role.objects.get(name='Staff')
                user.role = default_role
                user.save()
            return Response({
                'status': 'success',
                'message': 'User created successfully.',
                'data': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetYourInfo(APIView):
    permission_classes = [IsAuthenticated, HasRolePermission]
    serializer_class = UserSerializer
    # required_permission = 'can_read_user'

    def get(self, request):
        host = request.user
        serializer = UserSerializer(host)
        return Response(serializer.data)

class GetUserView(ListAPIView):
    permission_classes = [HasRolePermission]
    required_permission = 'can_read_user'
    queryset=User.objects.all().order_by('id')
    serializer_class = GetUserSerializer
    pagination_class = CustomPageNumberPagination

class UpdateUserView(APIView):
    permission_classes = [HasRolePermission]
    required_permission = 'can_update_user'
    serializer_class = UserUpdateSerializer

    def get(self, request, pk=None):
        if pk is not None:
            user = User.objects.filter(pk=pk)
            if user:
                serializer = GetUserSerializer(user, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"msg": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk=None, format=None):
        user_to_update = User.objects.filter(pk=pk).first()
        if not user_to_update:
            return Response({"msg": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserUpdateSerializer(user_to_update, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'User successfully updated!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # refresh = RefreshToken.for_user(user)
            return Response({
                'status': 'success',
                'message': 'Login successful',
                'data': {
                    # 'refresh': str(refresh),
                    # 'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            
            return Response({
                'status': 'success',
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
# class HostAvailabilityView(APIView):
#     serializer_class = HostAvailabilitySerializer
#     # permission_classes = [HasRolePermission]
#     # required_permission = 'can_manage_availability'

#     def post(self, request):
#         serializer = HostAvailabilitySerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(host=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # Host views their availability slots
#     def get(self, request):
#         availabilities = HostAvailability.objects.filter(host=request.user)
#         serializer = HostAvailabilitySerializer(availabilities, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# class HostAvailabilityDetailView(APIView):
#     serializer_class = HostAvailabilitySerializer
#     # permission_classes = [HasRolePermission]
#     # required_permission = 'can_manage_availability'

#     def patch(self, request, pk):
#         availability = HostAvailability.objects.filter(pk=pk, host=request.user).first()
#         if not availability:
#             return Response({"error": "Availability slot not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         serializer = HostAvailabilitySerializer(availability, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk):
#         availability = HostAvailability.objects.filter(pk=pk, host=request.user).first()
#         if not availability:
#             return Response({"error": "Availability slot not found."}, status=status.HTTP_404_NOT_FOUND)
#         availability.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

class HostAvailabilityView(APIView): 
    serializer_class = HostAvailabilitySerializer
    permission_classes = [HasRolePermission]
    # required_permission = 'can_manage_availability'

    def post(self, request):
        serializer = HostAvailabilitySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(host=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        availabilities = HostAvailability.objects.filter(host=request.user)
        serializer = HostAvailabilitySerializer(availabilities, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class HostAvailabilityDetailView(APIView):
    serializer_class = HostAvailabilitySerializer
    permission_classes = [HasRolePermission]
    # required_permission = 'can_manage_availability'

    def patch(self, request, pk):
        availability = HostAvailability.objects.filter(pk=pk, host=request.user).first()
        if not availability:
            return Response({"error": "Availability slot not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = HostAvailabilitySerializer(
            availability, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        availability = HostAvailability.objects.filter(pk=pk, host=request.user).first()
        if not availability:
            return Response({"error": "Availability slot not found."}, status=status.HTTP_404_NOT_FOUND)
        availability.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

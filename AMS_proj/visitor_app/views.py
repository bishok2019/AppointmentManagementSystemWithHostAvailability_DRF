from .models import Visitor
from .serializers import VisitorSerializer, VisitorInfoSerializer, RescheduleSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from host_app.permissions import HasRolePermission
from custom_pagination import CustomPageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import VisitorFilter
from host_app.serializers import HostAvailabilitySerializer
from host_app.models import HostAvailability
# Create your views here.
class RegisterVisitorView(APIView):
    serializer_class = VisitorSerializer
    permission_classes = [AllowAny]
    def post(self, request, pk=None):
        registration_serializer = VisitorSerializer(data=request.data)
        availabilities = HostAvailability.objects.filter(host=request.user, is_booked=False)
        availability_serializer = HostAvailabilitySerializer(availabilities, many=True, context={'request': request})
        if registration_serializer.is_valid():
            visitor = registration_serializer.save()
            display_serializer = VisitorInfoSerializer(visitor)
            return Response({'msg':'Meeting Appointed','data':display_serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'msg':registration_serializer.errors, 'available_slots':availability_serializer.data}, status=status.HTTP_400_BAD_REQUEST)

class VisitorView(ListAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorInfoSerializer
    # permission_classes = [HasRolePermission]
    # required_permission =  'can_read_visitor'
    pagination_class=CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = VisitorFilter

class UpdateVisitorView(APIView):
    serializer_class = VisitorSerializer
    # permission_classes = [HasRolePermission]
    # required_permission =  'can_update_visitor'
    def get(self, request, pk=None):
        if pk is not None:
            visitors = Visitor.objects.filter(pk=pk).first()
            if visitors:
                serializer = VisitorSerializer(visitors)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"msg": "Visitor not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, pk=None, format=None):
        visitor = Visitor.objects.filter(pk=pk).first()
        if not visitor:
            return Response({"msg": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = VisitorSerializer(visitor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Visitor successfully updated!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        

# class YourAppointmentView(APIView): # Doesnot include pagination
#     permission_classes = [IsAuthenticated]
#     serializer_class = RescheduleSerializer
#     pagination_class=CustomPageNumberPagination

#     def get(self, request, pk=None):
#         host = request.user
#         visitor = Visitor.objects.filter(visiting_to=host)
#         if visitor.exists():
#             serializer = VisitorInfoSerializer(visitor, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response({"msg": "You have no appointments."}, status=status.HTTP_404_NOT_FOUND)

class YourAppointmentView(APIView): # Does include pagination but no navigation
    permission_classes = [IsAuthenticated]
    # serializer_class = VisitorSerializer # We dont need to include if it is incuded in get method as below
    pagination_class=CustomPageNumberPagination

    def get(self, request, pk=None):
        host = request.user
        visitor = Visitor.objects.filter(visiting_to=host)
        if not visitor.exists():
            return Response({"msg": "You have no appointments."}, status=status.HTTP_404_NOT_FOUND)
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(visitor, request)
        serializer = VisitorInfoSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

# class YourAppointmentView(ListAPIView): # Include pagination with navigation
#     permission_classes = [IsAuthenticated]
#     serializer_class = VisitorInfoSerializer
#     pagination_class=CustomPageNumberPagination

#     def get_queryset(self):
#         host = self.request.user
#         queryset = Visitor.objects.filter(visiting_to=host)
#         if not queryset.exists():
#             self.no_appointments = True
#         else:
#             self.no_appointments = False
#         return queryset

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         if hasattr(self, "no_appointments") and self.no_appointments:
#             return Response({"msg": "You have no appointments."}, status=status.HTTP_404_NOT_FOUND)
#         return super().list(request, *args, **kwargs)

class UpdateYourAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RescheduleSerializer
    # required_permission = 'can_update_appointment'

    def get(self, request, pk=None):
        host = request.user
        if pk is not None:
            visitors = Visitor.objects.filter(pk=pk, visiting_to=host).first()
            if visitors:
                serializer = RescheduleSerializer(visitors)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"msg": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk=None, format=None):
        host = request.user
        visitor = Visitor.objects.filter(pk=pk, visiting_to=host).first()
        if not visitor:
            return Response({"msg": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = RescheduleSerializer(visitor, data=request.data, partial=True)
        availabilities = HostAvailability.objects.filter(host=request.user)
        availability_serializer = HostAvailabilitySerializer(availabilities, many=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Appointment successfully rescheduled!'}, status=status.HTTP_200_OK)
        return Response({'msg':serializer.errors,'availability':availability_serializer.data}, status=status.HTTP_400_BAD_REQUEST)
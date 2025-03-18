from django_filters import rest_framework as filters
from .models import Visitor

class VisitorFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    meeting_date_from = filters.DateTimeFilter(field_name='meeting_date', lookup_expr='gte')
    meeting_date_to = filters.DateTimeFilter(field_name='meeting_date', lookup_expr='lte')
    
    class Meta:
        model = Visitor
        fields = ['name', 'email', 'status', 'meeting_date']
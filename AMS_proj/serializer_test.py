from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Visitor
from host_app.models import HostAvailability
from notification.services import create_notification
from datetime import datetime

class TimeValidationMixin:
    def validate_times(self, data):
        """Common time validation logic for all serializers"""
        instance = getattr(self, 'instance', None)
        
        # Get values from data or existing instance
        meeting_date = data.get('meeting_date') or (instance.meeting_date if instance else None)
        start_time = data.get('meeting_start_time') or (instance.meeting_start_time if instance else None)
        end_time = data.get('meeting_end_time') or (instance.meeting_end_time if instance else None)

        # Null check first
        if None in [meeting_date, start_time, end_time]:
            raise serializers.ValidationError("All time fields are required")

        # Create timezone-aware datetime objects
        meeting_start = timezone.make_aware(
            datetime.combine(meeting_date, start_time))
        meeting_end = timezone.make_aware(
            datetime.combine(meeting_date, end_time))
        now = timezone.now()

        # Validation checks
        if meeting_start >= meeting_end:
            raise serializers.ValidationError("End time must be after start time")
            
        if (meeting_end - meeting_start).total_seconds() < 900:
            raise serializers.ValidationError("Minimum 15 minutes required")
            
        if meeting_start < now:
            raise serializers.ValidationError("Cannot schedule meetings in the past")

        return data

class NotificationMixin:
    def send_status_notification(self, instance, old_status):
        """Handle common notification logic"""
        if instance.status != old_status:
            create_notification(
                recipient=instance.visiting_to,
                notification_type='STATUS_CHANGE',
                title=f'Status Update - {instance.name}',
                message=f'Status changed from {old_status} to {instance.status}',
                content_object=instance,
                actor=self.context['request'].user
            )

    def send_schedule_notification(self, instance, original_schedule):
        """Notify about schedule changes"""
        old_date, old_start, old_end = original_schedule
        if (instance.meeting_date != old_date or
            instance.meeting_start_time != old_start or
            instance.meeting_end_time != old_end):
            
            create_notification(
                recipient=instance.visiting_to,
                notification_type='SCHEDULE_CHANGE',
                title=f'Schedule Update - {instance.name}',
                message=f'Meeting rescheduled to {instance.meeting_date} {instance.meeting_start_time}-{instance.meeting_end_time}',
                content_object=instance,
                actor=self.context['request'].user
            )

class BaseVisitorSerializer(TimeValidationMixin, NotificationMixin, serializers.ModelSerializer):
    department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'company', 'email', 'photo', 'phone_num', 'status',
            'visiting_to', 'meeting_date', 'meeting_start_time', 'meeting_end_time',
            'reason', 'department'
        ]
        read_only_fields = ['status']

    def validate(self, data):
        data = super().validate(data)
        data = self.validate_times(data)
        self.check_availability(data)
        return data

    def check_availability(self, data):
        """Common availability check logic"""
        if self.context['request'].method == 'POST':
            # Only check availability for new appointments
            overlapping = HostAvailability.objects.filter(
                host=data['visiting_to'],
                date=data['meeting_date'],
                start_time__lte=data['meeting_start_time'],
                end_time__gte=data['meeting_end_time'],
                is_approved=True,
                is_booked=False
            ).exists()
            
            if not overlapping:
                raise serializers.ValidationError("No available slot for this time")

class VisitorSerializer(BaseVisitorSerializer):
    """For new visitor creation"""
    def create(self, validated_data):
        visitor = super().create(validated_data)
        create_notification(
            recipient=visitor.visiting_to,
            notification_type='NEW_VISITOR',
            title='New Visitor Request',
            message=f'New request from {visitor.name}',
            content_object=visitor,
            actor=self.context['request'].user
        )
        return visitor

class UpdateVisitorSerializer(BaseVisitorSerializer):
    """For general updates"""
    class Meta(BaseVisitorSerializer.Meta):
        read_only_fields = BaseVisitorSerializer.Meta.read_only_fields + ['visiting_to']

    def validate(self, data):
        data = super().validate(data)
        if self.instance.status == 'confirmed':
            raise serializers.ValidationError("Confirmed appointments cannot be modified")
        return data

    def update(self, instance, validated_data):
        original_status = instance.status
        original_schedule = (
            instance.meeting_date,
            instance.meeting_start_time,
            instance.meeting_end_time
        )
        
        instance = super().update(instance, validated_data)
        
        self.send_status_notification(instance, original_status)
        self.send_schedule_notification(instance, original_schedule)
        
        return instance

class RescheduleSerializer(BaseVisitorSerializer):
    """Specialized for rescheduling operations"""
    class Meta(BaseVisitorSerializer.Meta):
        fields = BaseVisitorSerializer.Meta.fields + ['availability']
        read_only_fields = BaseVisitorSerializer.Meta.read_only_fields + ['visiting_to']

    @transaction.atomic
    def update(self, instance, validated_data):
        original_schedule = (
            instance.meeting_date,
            instance.meeting_start_time,
            instance.meeting_end_time
        )
        
        # Store old availability before update
        old_availability = instance.availability
        
        instance = super().update(instance, validated_data)
        
        # Handle availability slot changes
        if 'availability' in validated_data:
            new_availability = validated_data['availability']
            self.update_availability_slots(old_availability, new_availability)
        
        self.send_schedule_notification(instance, original_schedule)
        return instance

    def update_availability_slots(self, old_slot, new_slot):
        """Handle availability slot management"""
        if old_slot:
            old_slot.is_booked = False
            old_slot.save()
        
        new_slot.is_booked = True
        new_slot.save()
        new_slot.refresh_from_db()
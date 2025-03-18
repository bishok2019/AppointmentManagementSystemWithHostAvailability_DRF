from django.db import transaction
from rest_framework import serializers
from .models import Visitor
from host_app.models import HostAvailability
from datetime import datetime
from notify_with_email import send_creation_notifications, send_update_notification

class VisitorSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    meeting_duration = serializers.SerializerMethodField()
    # visiting_to = serializers.CharField(source='visiting_to.username')

    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'company', 'email', 'photo', 'phone_num', 'status',
            'visiting_to', 'meeting_date', 'meeting_start_time', 'meeting_end_time',
            'meeting_duration', 'reason', 'department'
        ]
        read_only_fields = ['status']

    def get_meeting_duration(self, obj):
        start = datetime.combine(obj.meeting_date, obj.meeting_start_time)
        end = datetime.combine(obj.meeting_date, obj.meeting_end_time)
        return int((end - start).total_seconds() // 60)

    def validate(self, data):
        meeting_date = data.get('meeting_date')
        meeting_start = data.get('meeting_start_time')
        meeting_end = data.get('meeting_end_time')

        if meeting_end <= meeting_start:
            raise serializers.ValidationError("End time must be after start time")
            
        if (datetime.combine(meeting_date, meeting_end) - 
            datetime.combine(meeting_date, meeting_start)).total_seconds() < 900:
            raise serializers.ValidationError("Minimum 15 minutes required")

        return data

    def create(self, validated_data):
    #Create visitor without linking to HostAvailability
        visitor = Visitor.objects.create(
            name=validated_data['name'],
            company=validated_data['company'],
            email=validated_data['email'],
            phone_num=validated_data['phone_num'],
            visiting_to=validated_data['visiting_to'],
            meeting_date=validated_data['meeting_date'],
            meeting_start_time=validated_data['meeting_start_time'],
            meeting_end_time=validated_data['meeting_end_time'],
            reason=validated_data['reason'],
            status='pending'  # Initial status
        )
        send_creation_notifications(visitor)
        return visitor

class RescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = ['id', 'meeting_date', 'meeting_start_time', 
                  'meeting_end_time', 'status']
        read_only_fields = ['visiting_to']

    def validate(self, data):
        instance = self.instance
        if instance.status == 'confirmed':
            raise serializers.ValidationError("Confirmed appointments cannot be modified.")

        new_date = data.get('meeting_date', instance.meeting_date)
        new_start = data.get('meeting_start_time', instance.meeting_start_time)
        new_end = data.get('meeting_end_time', instance.meeting_end_time)
        host = instance.visiting_to

        if new_end <= new_start:
            raise serializers.ValidationError("End time must be after start time")
            
        if (datetime.combine(new_date, new_end) - datetime.combine(new_date, new_start)).total_seconds() < 900:
            raise serializers.ValidationError("Minimum 15 minutes required")

        # Check for conflicts with other appointments
        overlapping = Visitor.objects.filter(
            visiting_to=host,
            meeting_date=new_date,
            meeting_start_time__lt=new_end,
            meeting_end_time__gt=new_start
        ).exclude(id=instance.id).exclude(status='cancelled').exists()

        if overlapping:
            raise serializers.ValidationError("Time slot already booked")

        # For confirmation, check extended availability
        if data.get('status') == 'confirmed':
            availability = HostAvailability.objects.filter(
                host=host,
                date=new_date,
                start_time__lte=new_start,
                end_time__gte=new_end,
                is_approved=True,
                is_booked=False
            ).first()

            if not availability:
                raise serializers.ValidationError("No available slot for confirmation")

            data['availability'] = availability

        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        
        if new_status != 'confirmed':
            # Handle non-confirmed updates
            instance.meeting_date = validated_data.get('meeting_date', instance.meeting_date)
            instance.meeting_start_time = validated_data.get('meeting_start_time', instance.meeting_start_time)
            instance.meeting_end_time = validated_data.get('meeting_end_time', instance.meeting_end_time)
            instance.save()
            send_update_notification(instance)
            return instance

        # Confirmation-specific logic
        availability = validated_data['availability']  # Use validated availability

        # Create new booked slot
        booked_slot = HostAvailability.objects.create(
            host=availability.host,
            date=validated_data.get('meeting_date', instance.meeting_date),
            start_time=validated_data.get('meeting_start_time', instance.meeting_start_time),
            end_time=validated_data.get('meeting_end_time', instance.meeting_end_time),
            is_approved=True,
            is_booked=True
            )

        # Split remaining availability
        if availability.start_time < booked_slot.start_time:
            HostAvailability.objects.create(
                host=availability.host,
                date=availability.date,
                start_time=availability.start_time,
                end_time=booked_slot.start_time,
                is_approved=True,
                is_booked=False
            )

        if availability.end_time > booked_slot.end_time:
            HostAvailability.objects.create(
                host=availability.host,
                date=availability.date,
                start_time=booked_slot.end_time,
                end_time=availability.end_time,
                is_approved=True,
                is_booked=False
            )

        availability.delete()  # Delete the original validated slot

        # Update visitor instance
        instance.availability = booked_slot
        instance.status = 'confirmed'
        instance.meeting_date = validated_data.get('meeting_date', instance.meeting_date)
        instance.meeting_start_time = validated_data.get('meeting_start_time', instance.meeting_start_time)
        instance.meeting_end_time = validated_data.get('meeting_end_time', instance.meeting_end_time)
        instance.save()

        self.merge_slots(booked_slot.host, booked_slot.date)
        send_update_notification(instance)
        return instance

    def merge_slots(self, host, date):
        slots = HostAvailability.objects.filter(
            host=host,
            date=date,
            is_booked=False,
            is_approved=True
        ).order_by('start_time')

        current = None
        for slot in slots:
            if not current:
                current = slot
            elif current.end_time == slot.start_time:
                current.end_time = slot.end_time
                current.save()
                slot.delete()
            else:
                current = slot

class VisitorInfoSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    visiting_to = serializers.CharField(source='visiting_to.username', read_only=True)
    meeting_duration = serializers.SerializerMethodField()

    class Meta:
        model = Visitor
        fields = ['id', 'name', 'email', 'photo', 'phone_num', 'status', 'visiting_to', 
                  'meeting_date', 'meeting_start_time', 'meeting_end_time', 'meeting_duration', 
                  'reason', 'department']
        read_only_fields = ['status']

    def get_meeting_duration(self, obj):
        start_datetime = datetime.combine(obj.meeting_date, obj.meeting_start_time)
        end_datetime = datetime.combine(obj.meeting_date, obj.meeting_end_time)
        meeting_duration = end_datetime - start_datetime
        return int(meeting_duration.total_seconds() // 60)
from django.utils import timezone
from notification.services import create_notification
from django.db import transaction
from rest_framework import serializers
from .models import Visitor
from host_app.models import HostAvailability
from datetime import datetime
from notify_with_email import send_creation_notifications, send_update_notification
from django.utils import timezone

class VisitorSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    meeting_duration = serializers.ReadOnlyField()
    # visiting_to = serializers.CharField(source='visiting_to.username')

    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'company', 'email', 'photo', 'phone_num', 'status',
            'visiting_to', 'meeting_date', 'meeting_start_time', 'meeting_end_time',
            'meeting_duration', 'reason', 'department'
        ]
        read_only_fields = ['status']

    def validate(self, data):
        meeting_date = data.get('meeting_date')
        start_time = data.get('meeting_start_time')
        end_time = data.get('meeting_end_time')

        if meeting_date and start_time:

            meeting_datetime = timezone.make_aware(datetime.combine(meeting_date, start_time),timezone.get_current_timezone())
            
            now = timezone.now()

            if meeting_datetime < now:
                raise serializers.ValidationError("Meeting cannot be scheduled in the past.")
        
        # End time must be after start time
        if end_time <= start_time:
            raise serializers.ValidationError("End time must be after start time")
        
        # # Minimum 15 minutes required
        if meeting_date and start_time and end_time:
            duration = (datetime.combine(meeting_date, end_time) - datetime.combine(meeting_date, start_time)).total_seconds()
            if duration < 900:
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
            status='pending'
        )
        send_creation_notifications(visitor)

        create_notification(
            recipient=visitor.visiting_to,
            notification_type='VISITOR_REQUEST',
            title='New Visitor Request',
            message=f'New visitor request from {visitor.name}',
            content_object=visitor
        )
        return visitor
class UpdateVisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'company', 'email', 'photo', 'phone_num', 'status',
            'visiting_to', 'meeting_date', 'meeting_start_time', 'meeting_end_time',
            'meeting_duration', 'reason'
        ]
        read_only_fields = ['status']

    def validate(self, data):
        instance = self.instance
        # Check if the status is confirmed
        if instance.status == 'confirmed':
            raise serializers.ValidationError("Confirmed appointments cannot be modified.")

        visiting_to = data.get('visiting_to', self.instance.visiting_to)
        meeting_date = data.get('meeting_date', self.instance.meeting_date)
        meeting_start = data.get('meeting_start_time', self.instance.meeting_start_time)
        meeting_end = data.get('meeting_end_time', self.instance.meeting_end_time)

        # Meeting cannot be scheduled in the past
        if meeting_date and meeting_start:

            meeting_datetime = timezone.make_aware(datetime.combine(meeting_date, meeting_start),timezone.get_current_timezone())
            
            now = timezone.now()

            if meeting_datetime < now:
                raise serializers.ValidationError("Meeting cannot be scheduled in the past.")
            
        # End time must be after start time
        if meeting_end <= meeting_start:
            raise serializers.ValidationError("End time must be after start time")
    
        if (datetime.combine(meeting_date, meeting_end) - datetime.combine(meeting_date, meeting_start)).total_seconds() < 900:
            raise serializers.ValidationError("Minimum 15 minutes required")
        

        # Overlap check: Only check against active statuses (confirmed, checked_in, completed)
        overlapping = Visitor.objects.filter(
            visiting_to=visiting_to,
            meeting_date=meeting_date,
            meeting_start_time__lt=meeting_end,
            meeting_end_time__gt=meeting_start,
            status__in=['confirmed', 'checked_in', 'completed']  # Exclude pending/cancelled
        ).exclude(pk=instance.pk)  # Exclude current appointment

        if overlapping.exists():
            raise serializers.ValidationError("This time slot overlaps with an active appointment for the host.")


        return data

    def update(self, instance, validated_data):
        old_host = None
        original_status = instance.status
        
        # Check if the host is being changed
        if 'visiting_to' in validated_data and instance.visiting_to != validated_data['visiting_to']:
            old_host = instance.visiting_to  # Capture old host

        instance.modified_by = self.context['request'].user # This is logged in user we need to capture
        
        # Update the instance
        instance = super().update(instance, validated_data)
        new_status = instance.status

        #Notification logic
        if old_host:
            #Notify Old Host
            create_notification(
                recipient=old_host,
                notification_type='VISITOR_UPDATE',
                title=f'Visitor Reassigned - {instance.name}',
                message=f'Visitor {instance.name} has been removed from your list.',
                content_object=instance
            )
            #Notify New Host
            create_notification(
                recipient=instance.visiting_to,
                notification_type='VISITOR_UPDATE',
                title=f'Visitor Assigned - {instance.name}',
                message=f'Visitor {instance.name} has been assigned to you by {instance.modified_by.username}.',
                content_object=instance
            )

            # Status change notification
        if new_status != original_status:
            create_notification(
                recipient=instance.visiting_to,
                notification_type='VISITOR_UPDATE',
                title=f'Status Update - {instance.name}',
                message=f'Status changed to {new_status} by {instance.modified_by.username}.',
                content_object=instance
            )
        
        # Trigger notifications (host change or general update)
        send_update_notification(instance, old_host=old_host) # for email
        
        return instance

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

        if new_date and new_start:
            meeting_datetime = timezone.make_aware(datetime.combine(new_date, new_start))
            if meeting_datetime < timezone.now():
                raise serializers.ValidationError("Meeting cannot be scheduled in the past.")

        if new_end <= new_start:
            raise serializers.ValidationError("End time must be after start time")
            
        if (datetime.combine(new_date, new_end) - datetime.combine(new_date, new_start)).total_seconds() < 900:
            raise serializers.ValidationError("Minimum 15 minutes required")

        # Check for conflicts with other appointments
        overlapping = Visitor.objects.filter(
            visiting_to=host,
            meeting_date=new_date,
            meeting_start_time__lt=new_end,
            meeting_end_time__gt=new_start,
        ).exclude(id=instance.id).exclude(status__in=['cancelled','pending']).exists()

        if overlapping:
            raise serializers.ValidationError("The time slot for requested appointment is already booked")

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
            instance.reminder_for_a_day_before_meeting_sent = False
            instance.reminder_for_a_day_of_meeting_sent = False
            instance.reminder_for_a_five_minute_before_meeting_sent = False
            instance.status = new_status
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

        #create notification
        create_notification(
        recipient=instance.visiting_to,
        notification_type='VISITOR_UPDATE',
        title='Appointment Rescheduled',
        message=f'Your appointment with {instance.name} has been rescheduled to {instance.meeting_date}',
        content_object=instance
    )
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
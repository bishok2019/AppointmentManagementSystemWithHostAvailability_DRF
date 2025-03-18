from django.db import transaction
from rest_framework import serializers
from .models import Visitor
from host_app.models import HostAvailability
from datetime import datetime
from notify_with_email import send_creation_notifications, send_update_notification

class VisitorSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    meeting_duration = serializers.SerializerMethodField()

    class Meta:
        model = Visitor
        fields = ['id', 'name', 'company', 'email', 'photo', 'phone_num', 'status', 'visiting_to', 'meeting_date', 'meeting_start_time', 'meeting_end_time', 'meeting_duration','reason', 'department']
        read_only_fields = ['status']
    
    def get_meeting_duration(self, obj):
        start_datetime = datetime.combine(obj.meeting_date, obj.meeting_start_time)
        end_datetime = datetime.combine(obj.meeting_date, obj.meeting_end_time)
        meeting_duration = end_datetime - start_datetime
        return int(meeting_duration.total_seconds() // 60)
    
    def validate(self, data):
        meeting_date = data.get('meeting_date')
        meeting_start = data.get('meeting_start_time')
        meeting_end = data.get('meeting_end_time')
        host = data.get('visiting_to')

        # Basic time validation
        if meeting_end <= meeting_start:
            raise serializers.ValidationError({
                'meeting_end_time': 'Meeting end time must be after start time'
            })

        # Ensure meeting duration is at least 15 minutes
        if (datetime.combine(meeting_date, meeting_end) - datetime.combine(meeting_date, meeting_start)).total_seconds() < 900:
            raise serializers.ValidationError({
                'meeting_duration': 'Meeting must be at least 15 minutes long'
            })

        # available_slot= HostAvailability.objects.filter(host=host, is_booked=False).first()
        # # Check if host has availability configured for the requested date
        # if not HostAvailability.objects.filter(host=host, date=meeting_date).exists():
        #     raise serializers.ValidationError({
        #         'msg': 'Host has no availability  for requested date',
        #         'available slots':f'{available_slot}'
        #     })

        # Find the earliest available slot for the host on the requested date
        earliest_availability = HostAvailability.objects.filter(
            host=host,
            date=meeting_date,
            is_approved=True,
            is_booked=False
        ).order_by('start_time').first()

        if not earliest_availability:
            raise serializers.ValidationError({
                'msg': 'Host has no available slots for this date'
            })

        # Check if meeting start time is before the host's earliest availability
        if meeting_start < earliest_availability.start_time:
            raise serializers.ValidationError({
                'meeting_start_time': f'Host is not available before {earliest_availability.start_time}. Please choose a later start time.'
            })

        # Check if meeting end time is after the host's latest availability
        latest_availability = HostAvailability.objects.filter(
            host=host,
            date=meeting_date,
            is_approved=True,
            is_booked=False
        ).order_by('-end_time').first()

        if meeting_end > latest_availability.end_time:
            raise serializers.ValidationError({
                'meeting_end_time': f'Host is not available after {latest_availability.end_time}. Please choose an earlier end time.'
            })

        # Find a slot that fully contains the requested meeting time
        availability = HostAvailability.objects.filter(
            host=host,
            date=meeting_date,
            start_time__lte=meeting_start,
            end_time__gte=meeting_end,
            is_approved=True,
            is_booked=False
        ).first()

        if not availability:
            raise serializers.ValidationError({'msg':'No available slot for the requested time'})

        data['availability'] = availability
        return data

    def create(self, validated_data):
        # when visitor book appointmenr the original availability of host will be splitted into parts
        # so we need to pop the original, 
        # later we will recerate different time slots for booked and remaining time slots
        availability = validated_data.pop('availability')
        meeting_start_time = validated_data['meeting_start_time']
        meeting_end_time = validated_data['meeting_end_time']

        # Create the booked time slot
        booked_slot = HostAvailability.objects.create(
            host=availability.host,
            date=availability.date,
            start_time=meeting_start_time,
            end_time=meeting_end_time,
            is_approved=True,
            is_booked=False
        )

    # Create a time slot before the booked time if there is remaining time
        if availability.start_time < meeting_start_time:
            # First check if the remaining time before the booked slot is exist unbooked
            existing_slots = HostAvailability.objects.filter(
                host=availability.host,
                date=availability.date,
                start_time=availability.start_time,
                end_time=meeting_start_time,
                is_booked=True
            )
            # If exist unbooked, then create  new time slot
            if not existing_slots.exists():
                HostAvailability.objects.create(
                    host=availability.host,
                    date=availability.date,
                    start_time=availability.start_time,
                    end_time=meeting_start_time,
                    is_approved=True,
                    is_booked=False
                )

    # Create a time slot after the booked time if there is remaining time
        if availability.end_time > meeting_end_time:
            # First, check if the remaining time after the booked slot is exist unbooked

            existing_slots = HostAvailability.objects.filter(
                host=availability.host,
                date=availability.date,
                start_time=meeting_end_time,
                end_time=availability.end_time,
                is_booked=True
            )
            # If exist unbooked, then create  new time slot
            if not existing_slots.exists():
                HostAvailability.objects.create(
                    host=availability.host,
                    date=availability.date,
                    start_time=meeting_end_time,
                    end_time=availability.end_time,
                    is_approved=True,
                    is_booked=False
                )

    # Delete the original slot because the original time slot is now splited.
        availability.delete()

    # Save the visitor appointment linked to the booked slot
        validated_data['availability'] = booked_slot  # Assign booked slot to visitor
        visitor = Visitor.objects.create(**validated_data)
        # Send notifications to both visitor and host on creation
        send_creation_notifications(visitor)

        return visitor

class VisitorInfoSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    visiting_to = serializers.CharField(source='visiting_to.username', read_only=True)
    meeting_duration= serializers.SerializerMethodField()#

    class Meta:
        model = Visitor
        fields = ['id','name', 'email','photo','phone_num','status','visiting_to', 'meeting_date', 'meeting_start_time', 'meeting_end_time','meeting_duration','reason','department']
        read_only_fields = ['status']

    def get_meeting_duration(self, obj):
        start_datetime = datetime.combine(obj.meeting_date, obj.meeting_start_time)
        end_datetime = datetime.combine(obj.meeting_date, obj.meeting_end_time)
        meeting_duration = end_datetime - start_datetime
        return int(meeting_duration.total_seconds() // 60)

class RescheduleSerializer(serializers.ModelSerializer):
    visiting_to = serializers.CharField(source='visiting_to.username', read_only=True)

    class Meta:
        model = Visitor
        fields = ['id', 'name', 'meeting_date', 'meeting_start_time', 'meeting_end_time', 'status', 'visiting_to']
        read_only_fields = ['visiting_to']

    def validate(self, data):
        # Validate the updated meeting times
        instance = self.instance
        host = instance.visiting_to

        # Retrieve new meeting details
        new_start = data.get('meeting_start_time', instance.meeting_start_time)
        new_end = data.get('meeting_end_time', instance.meeting_end_time)
        new_date = data.get('meeting_date', instance.meeting_date)
        
        # Store original times for comparison
        old_start = instance.meeting_start_time
        old_end = instance.meeting_end_time
        old_date = instance.meeting_date

        # Ensure end time is after start time
        if new_end <= new_start:
            raise serializers.ValidationError({'msg':"End time must be after start time."})

        # Ensure the new meeting duration is at least 15 minutes
        if (datetime.combine(new_date, new_end) - datetime.combine(new_date, new_start)).total_seconds() < 900:
            raise serializers.ValidationError({'msg':"Meeting duration must be at least 15 minutes."})

        # Check for overlapping appointments (excluding the current one)
        overlapping = Visitor.objects.filter(
            visiting_to=host,
            meeting_date=new_date,
            meeting_start_time__lt=new_end,
            meeting_end_time__gt=new_start
        ).exclude(id=instance.id).exists()
        if overlapping:
            raise serializers.ValidationError({'msg':"Cannot Book! Other appointment exist between the time duration you requested."})

        # Handle special case for modifying the current appointment's time
        # Determine if we're extending or reducing the appointment
        extending_start = new_start < old_start
        extending_end = new_end > old_end
        reducing_start = new_start > old_start
        reducing_end = new_end < old_end
        
        #  Reducing appointment duration (making it start later or end earlier)
        if (reducing_start and not extending_end) or (reducing_end and not extending_start):
            # When reducing duration, we're just freeing up part of an already booked slot
            # So we should always allow this change if there are no conflicts
            data.update({
                'merged_slots': [instance.availability],  # Pass the current slot to be modified
                'merged_start': new_start,
                'merged_end': new_end,
                'extending_start': False,
                'extending_end': False,
                'current_slot': instance.availability
            })
            return data
        
        # extending appointment duration (starting earlier or ending later)
        if extending_start or extending_end:
            # Find available slots for the extension part only
            if extending_start:
                # Check if there's available time before the current appointment
                extension_coverage = HostAvailability.find_available_coverage(
                    host, new_date, new_start, old_start, exclude_slot=None
                )
                if not extension_coverage:
                    raise serializers.ValidationError({'msg':"Cannot extend earlier - no available time slots."})
            
            if extending_end:
                # Check if there's available time after the current appointment
                extension_coverage = HostAvailability.find_available_coverage(
                    host, new_date, old_end, new_end, exclude_slot=None
                )
                if not extension_coverage:
                    raise serializers.ValidationError({'msg':"Cannot extend later - no available time slots."})
        
        # For all cases, we need to ensure the full requested time slot is available
        # This includes the current slot (which we exclude) plus any available adjacent slots
        all_coverage = HostAvailability.find_available_coverage(
            host, new_date, new_start, new_end, exclude_slot=instance.availability
        )
        
        # Combine the current slot with found coverage
        current_slot = {
            'slot': instance.availability,
            'start': instance.meeting_start_time,
            'end': instance.meeting_end_time
        }
        
        # If no additional coverage needed (or found), just use the current slot
        merged_coverage = [current_slot]
        
        # If additional coverage found, merge it
        if all_coverage:
            merged_coverage.extend(all_coverage)
        
        # Sort by start time
        merged_coverage.sort(key=lambda x: x['start'])
        
        # Check for gaps in coverage
        full_coverage = True
        prev_end = new_start
        for slot in merged_coverage:
            slot_start = max(slot['start'], new_start)
            slot_end = min(slot['end'], new_end)
            
            if slot_start > prev_end:
                full_coverage = False
                break
            
            prev_end = max(prev_end, slot_end)
        
        if prev_end < new_end:
            full_coverage = False
        
        if not full_coverage:
            raise serializers.ValidationError({'msg':"Requested time is not fully available."})
        
        # Store slots and new times
        slots_to_merge = [slot['slot'] for slot in all_coverage] if all_coverage else []
        if not extending_start and not extending_end:
            # For simple rescheduling, include the current slot
            slots_to_merge.append(instance.availability)
        
        data.update({
            'merged_slots': slots_to_merge,
            'merged_start': new_start,
            'merged_end': new_end,
            'extending_start': extending_start,
            'extending_end': extending_end,
            'current_slot': instance.availability
        })
        
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        # Get flags and data from validation
        extending_start = validated_data.pop('extending_start', False)
        extending_end = validated_data.pop('extending_end', False)
        current_slot = validated_data.pop('current_slot', None)
        
        # Get the old availability object
        old_availability = instance.availability
        merged_slots = validated_data.pop('merged_slots', [])
        new_start = validated_data.pop('merged_start')
        new_end = validated_data.pop('merged_end')

        # Handle different cases based on whether we're extending or reducing
        if extending_start or extending_end:
            # For extension, we need to:
            #  Release the old booking
            #  Create a new larger booking
            #  Adjust or delete any affected free slots
            
            # Release the old booking by making it available
            old_availability.is_booked = False
            old_availability.save()
            
            # Create new booked slot
            new_availability = HostAvailability.objects.create(
                host=old_availability.host,
                date=old_availability.date,
                start_time=new_start,
                end_time=new_end,
                is_approved=True,
                is_booked=True
            )
            
            # Process the free slots that we're consuming
            for slot in merged_slots:
                if slot.id != old_availability.id:  # Skip the original slot
                    if slot.start_time >= new_start and slot.end_time <= new_end:
                        # This free slot is completely consumed
                        slot.delete()
                    elif slot.start_time < new_start < slot.end_time:
                        # Only consume the latter part of this slot
                        slot.end_time = new_start
                        slot.save()
                    elif slot.start_time < new_end < slot.end_time:
                        # Only consume the earlier part of this slot
                        slot.start_time = new_end
                        slot.save()
            
            # Now delete the old availability slot as it's been replaced
            old_availability.delete()
        else:
            # For reduction, we need to:
            # reduce the current booking
            # Create free slots for the freed-up time
            
            # Handle start time change (moved later - creates free slot before)
            if new_start > old_availability.start_time:
                HostAvailability.objects.create(
                    host=old_availability.host,
                    date=old_availability.date,
                    start_time=old_availability.start_time,
                    end_time=new_start,
                    is_approved=True,
                    is_booked=False
                )
            
            # Handle end time change (moved earlier - creates free slot after)
            if new_end < old_availability.end_time:
                HostAvailability.objects.create(
                    host=old_availability.host,
                    date=old_availability.date,
                    start_time=new_end,
                    end_time=old_availability.end_time,
                    is_approved=True,
                    is_booked=False
                )
            
            # Update the current booking with new times
            old_availability.start_time = new_start
            old_availability.end_time = new_end
            old_availability.save()
            
            # Set the new availability for return value
            new_availability = old_availability

        # Update the Visitor appointment
        instance.meeting_start_time = new_start
        instance.meeting_end_time = new_end
        instance.availability = new_availability
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        # Merge adjacent free slots to reduce fragmentation
        self.merge_slots(new_availability.host, new_availability.date)

        # Send notification to the visitor only on updates
        send_update_notification(instance)

        return instance

    def merge_slots(self, host, date):
        # Merges adjacent free slots for better availability management
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

    def release_slot(self, availability, new_start, new_end):
        # Releases the original booked slot and preserves available time outside the new meeting window
        availability.is_booked = False
        availability.save()

        if availability.start_time < new_start:
            existing_slot = HostAvailability.objects.filter(
                host=availability.host,
                date=availability.date,
                start_time=availability.start_time,
                end_time=availability.end_time,
                is_booked=False
            ).first()

            if existing_slot:
                # update existing free slot instead of deleting it
                existing_slot.end_time = new_start
                existing_slot.save()
            else:
                # If no free slot exists, create a new one
                HostAvailability.objects.create(
                    host=availability.host,
                    date=availability.date,
                    start_time=availability.start_time,
                    end_time=new_start,
                    is_approved=True,
                    is_booked=False
                )
        
        #If there is free time after the new meeting, ensure it remains available
        if availability.end_time > new_end:
            HostAvailability.objects.create(
                host=availability.host,
                date=availability.date,
                start_time=new_end,
                end_time=availability.end_time,
                is_approved=True,
                is_booked=False
            )

        availability.delete()
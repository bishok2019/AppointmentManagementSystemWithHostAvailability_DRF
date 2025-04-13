from rest_framework import serializers
from .models import User, Department, HostAvailability
from django.contrib.auth import authenticate
from role_app.models import Role
from visitor_app.serializers import VisitorInfoSerializer
from datetime import datetime
from role_app.role_serializers import RoleDetailSerializer

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        
class HostAvailabilitySerializer(serializers.ModelSerializer):
    host = serializers.CharField(source='host.username', read_only=True)
    visitor = VisitorInfoSerializer(source='visitors', many=True, read_only=True)
    class Meta:
        model = HostAvailability
        fields = ['id', 'date', 'start_time', 'end_time', 'is_approved', 'host', 'is_booked', 'visitor']
        read_only_fields = ['visitor', 'host']

    def validate(self, data):
        # Validate timing rules and prevent overlaps (works for all operations)
        request = self.context.get('request')
        host = request.user if request else None

        # For updates, merge existing data with incoming data
        if self.instance:
            data = {
                'date': data.get('date', self.instance.date),
                'start_time': data.get('start_time', self.instance.start_time),
                'end_time': data.get('end_time', self.instance.end_time),
                'is_approved': data.get('is_approved', self.instance.is_approved),
            }

        start_time = data.get('start_time')
        end_time = data.get('end_time')
        date = data.get('date')

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        current_time = datetime.now().time()
        if date < datetime.today().date() or (date == datetime.today().date() and start_time < current_time):
            raise serializers.ValidationError("Cannot schedule in the past.")

        overlapping_slots = HostAvailability.objects.filter(
            host=host,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        if self.instance:
            overlapping_slots = overlapping_slots.exclude(id=self.instance.id)

        if overlapping_slots.exists():
            raise serializers.ValidationError("Availability already exists.")

        return data

    def create(self, validated_data):
        """Handle CREATE requests (POST)."""
        validated_data['host'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.date = validated_data.get('date', instance.date)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        instance.is_approved = validated_data.get('is_approved', instance.is_approved)
        instance.save()
        return instance
    
class UserSerializer(serializers.ModelSerializer):
    availability =HostAvailabilitySerializer(source='availabilities',read_only = True, many=True)
    password = serializers.CharField(write_only=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=True, write_only = True)
    depart = serializers.CharField(source='department.name', read_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False, allow_null=True, write_only=True,many=True)
    # It is used when you have to specify method like get in below.
    action = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password','department','depart','role','action','availability')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        host = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            department=validated_data['department']
        )
        return host
    
    def get_action(self, obj):
        roles = obj.role.all()
        return ", ".join(role.name for role in roles) or None
 
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)

            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Must include "email" and "password".')

class GetUserSerializer(serializers.ModelSerializer):
    role=RoleDetailSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id','username','department','email','role','is_active']

class UserUpdateSerializer(serializers.ModelSerializer):
    # department = serializers.CharField(source='visiting_to.department.name', read_only=True)
    depart = serializers.CharField(source='department.name', read_only=True)

    action = serializers.SerializerMethodField()
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False, allow_null=True, write_only=True,many=True)

    # This willnot work because it expect single role but its have manytomany relation with user
    # action = serializers.CharField(source='role.name', default="", read_only=True)

    class Meta:
        model = User
        fields = ['id','username','department','email','role','is_active','action','depart']
        read_only_fields = ['id', 'username']

    def get_action(self, obj):
        roles = obj.role.all()
        return ", ".join(role.name for role in roles) or None

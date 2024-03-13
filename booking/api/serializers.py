from account.models import Doctor, Patient, User
from rest_framework import serializers
from booking.models import DoctorAvailability, Transaction
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError





class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = '__all__'


class DoctorSlotUpdateSerializer(serializers.Serializer):
    date = serializers.DateField()
    slots = serializers.ListField(child=serializers.DictField())

    def validate(self, data):
        date = data.get('date')
        slots = data.get('slots')

        for slot_data in slots:
            from_time = datetime.strptime(slot_data.get('from_time'), '%H:%M:%S')
            to_time = datetime.strptime(slot_data.get('to_time'), '%H:%M:%S')

            # Check if the slot already exists for the specified date and time range
            if DoctorAvailability.objects.filter(doctor=self.context.get('doctor'), day=date, start_time__lt=to_time, end_time__gt=from_time).exists():
                raise ValidationError("Overlapping slots are not allowed.", code='overlap_error')

        return data

    def update_doctor_slots(self, doctor):
        try:
            date = self.validated_data.get('date')
            for slot_data in self.validated_data.get('slots'):
                from_time = datetime.strptime(slot_data.get('from_time'), '%H:%M:%S')
                to_time = datetime.strptime(slot_data.get('to_time'), '%H:%M:%S')

                DoctorAvailability.objects.create(
                    doctor=doctor,
                    day=date,
                    start_time=from_time,
                    end_time=to_time
                )

            return True

        except Exception as e:
            raise serializers.ValidationError(f"Error updating doctor slots: {str(e)}")



# for updating the slot of a long time period
        

class DoctorSlotBulkUpdateSerializer(serializers.Serializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    slots = serializers.ListField(child=serializers.DictField())

    def validate(self, data):
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        slots = data.get('slots')

        if len(slots) != 1:
            raise ValidationError("Only one time slot is allowed for the entire date range.", code='invalid_slots')

        slot_data = slots[0]
        from_time = datetime.strptime(slot_data.get('from_time'), '%H:%M:%S')
        to_time = datetime.strptime(slot_data.get('to_time'), '%H:%M:%S')

        if from_time >= to_time:
            raise ValidationError("Invalid time range. 'from_time' should be before 'to_time'.", code='invalid_time_range')

        return data

    def update_doctor_slots(self, doctor):
        try:
            from_date = self.validated_data['from_date']
            to_date = self.validated_data['to_date']
            slots = self.validated_data['slots']
            slot_data = slots[0]  # Only one slot is allowed

            current_date = from_date
            while current_date <= to_date:
                date_str = current_date.strftime('%Y-%m-%d')
                from_time = datetime.strptime(slot_data['from_time'], '%H:%M:%S')
                to_time = datetime.strptime(slot_data['to_time'], '%H:%M:%S')

                # Check if the slot already exists for the specified date and time range
                if DoctorAvailability.objects.filter(doctor=doctor, day=current_date, start_time__lt=to_time, end_time__gt=from_time).exists():
                    raise ValidationError(f"Overlapping slots are not allowed for {date_str}.", code='overlap_error')

                DoctorAvailability.objects.create(
                    doctor=doctor,
                    day=current_date,
                    start_time=from_time,
                    end_time=to_time
                )

                current_date += timedelta(days=1)

            return True

        except Exception as e:
            raise serializers.ValidationError(f"Error updating doctor slots: {str(e)}")
        



# Advanced SlotBooking Serializer
        
from datetime import datetime, timedelta, time
from rest_framework import serializers


class AdvancedSlotUpdateSerializer(serializers.Serializer):
    fromDate = serializers.DateField()
    toDate = serializers.DateField()
    fromTimeInMinutes = serializers.TimeField()
    toTimeInMinutes = serializers.TimeField()
    bufferTimeInMinutes = serializers.IntegerField()
    fromBreakTimeInMinutes = serializers.TimeField()
    toBreakTimeInMinutes = serializers.TimeField()
    workingdaysOfWeek = serializers.ListField(child=serializers.CharField())
    slot_duration = serializers.IntegerField()

    def validate(self, data):
        from_date = data['fromDate']
        to_date = data['toDate']
        from_time = data['fromTimeInMinutes']
        to_time = data['toTimeInMinutes']
        buffer_time = data['bufferTimeInMinutes']
        break_start_time = data['fromBreakTimeInMinutes']
        break_end_time = data['toBreakTimeInMinutes']
        working_days = data['workingdaysOfWeek']
        slot_duration = data['slot_duration']

        if from_date > to_date:
            raise serializers.ValidationError("Invalid date range. 'fromDate' should be before or equal to 'toDate'.")

        if from_time >= to_time:
            raise serializers.ValidationError("Invalid time range. 'fromTimeInMinutes' should be before 'toTimeInMinutes'.")

        if break_start_time >= break_end_time:
            raise serializers.ValidationError("Invalid break time range. 'fromBreakTimeInMinutes' should be before 'toBreakTimeInMinutes'.")

        return data

    def update_doctor_slots(self, doctor):
        try:
            from_date = self.validated_data['fromDate']
            to_date = self.validated_data['toDate']
            working_days = self.validated_data['workingdaysOfWeek']
            slot_duration = self.validated_data['slot_duration']
            break_start_time = self.validated_data['fromBreakTimeInMinutes']
            break_end_time = self.validated_data['toBreakTimeInMinutes']
            from_time = self.validated_data['fromTimeInMinutes']
            to_time = self.validated_data['toTimeInMinutes']
            buffer_time = self.validated_data['bufferTimeInMinutes']

            current_date = from_date
            all_slots = []

            while current_date <= to_date:
                day_str = current_date.strftime('%Y-%m-%d')
                if current_date.weekday() in [self.get_weekday_number(weekday) for weekday in working_days]:
                    slots = self.create_slots_for_day(doctor, current_date, slot_duration, break_start_time, break_end_time, from_time, to_time, buffer_time)
                    all_slots.append({"day": day_str, "slots": slots})
                current_date += timedelta(days=1)

            return all_slots

        except Exception as e:
            raise serializers.ValidationError(f"Error updating doctor slots: {str(e)}")

    def create_slots_for_day(self, doctor, current_date, slot_duration, break_start_time, break_end_time, from_time, to_time, buffer_time):
        working_days = self.validated_data['workingdaysOfWeek']

        if current_date.weekday() not in [self.get_weekday_number(weekday) for weekday in working_days]:
            return []  # No slots for non-working days

        slots = []
        current_time = self.time_to_minutes(from_time)

        while current_time + (slot_duration + buffer_time) <= self.time_to_minutes(to_time):
            # Check if the current time falls within the break time range
            if break_start_time <= self.minutes_to_time(current_time) < break_end_time:
                current_time += slot_duration + buffer_time
                continue  # Skip slot creation during break time

            slot_start_time = self.minutes_to_time(current_time)
            slot_end_time = self.minutes_to_time(current_time + slot_duration)

            # Check for overlap or duplication of slots
            if not DoctorAvailability.objects.filter(doctor=doctor, day=current_date, start_time__lt=slot_end_time, end_time__gt=slot_start_time).exists():
                DoctorAvailability.objects.create(
                    doctor=doctor,
                    day=current_date,
                    start_time=slot_start_time,
                    end_time=slot_end_time
                )
                slots.append({"start_time": slot_start_time.strftime('%H:%M:%S'), "end_time": slot_end_time.strftime('%H:%M:%S')})

            current_time += slot_duration + buffer_time

        return slots


    @staticmethod
    def get_weekday_number(weekday):
        weekdays_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        return weekdays_map.get(weekday)

    @staticmethod
    def time_to_minutes(time_obj):
        return time_obj.hour * 60 + time_obj.minute

    @staticmethod
    def minutes_to_time(minutes):
        return time(minutes // 60, minutes % 60)




class DOCUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password', 'id' ,'is_staff','is_superuser','user_type')



class AdminDocUpdateSerializer(serializers.ModelSerializer):
    user=DOCUserSerializer()
    class Meta:
        model = Doctor
        fields='__all__' 
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {}) # this is used to pop out the user object and if it is not existing then we will assign a {} to it as default
        user_serializer = DOCUserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        return super().update(instance, validated_data)


class AdminPatientUpdateSerializer(serializers.ModelSerializer):
    user=DOCUserSerializer()
    class Meta:
        model = Patient
        fields='__all__' 
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {}) # this is used to pop out the user object and if it is not existing then we will assign a {} to it as default
        user_serializer = DOCUserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        return super().update(instance, validated_data)
    




# serializer used list out all the docotrs based on the filter


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'



class UserDetailsUpdateSerializer(serializers.ModelSerializer):
    doctor_user=DoctorSerializer(read_only=True)
    class Meta:
        model = User
        exclude = ('password','is_id_verified','is_email_verified','is_staff','is_superuser','user_type')   




# Docotr bookin serializer
        
class RazorpayOrderSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    currency = serializers.CharField()


class TranscationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [ 'payment_id', 'order_id', 'signature', 'amount', 'doctor_id', 'patient_id', 'booked_date', 'booked_from_time', 'booked_to_time']


class TranscationModelList(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'



# for to get the trasaction based on patient details
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'profile_picture']

class TransactionPatientSerializer(serializers.ModelSerializer):
    # Use the UserSerializer for the patient field
    patient = UserSerializer(source='patient.user', read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'       




# for apply leave on a date range for  the docotor and delete the slotes on that day
        
class DeleteSlotsSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    
            
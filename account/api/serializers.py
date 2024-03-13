from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from account.models import Doctor, Patient, Rating, User, Verification, Wallet

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken, Token,AccessToken
from django.core.validators import RegexValidator



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['first_name'] = user.first_name
        # ...
        
        return token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password', )



class DOCUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password', 'id' ,'is_staff','is_superuser','user_type','email','profile_picture')





class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'is_active', 'first_name', 'last_name', 'user_type', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        validated_data['is_active'] = True
        return super(UserRegisterSerializer, self).create(validated_data)



class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'



class UserDetailsUpdateSerializer(serializers.ModelSerializer):
    doctor_user=DoctorSerializer(read_only=True)
    class Meta:
        model = User
        exclude = ('password','is_id_verified','is_email_verified','is_staff','is_superuser','user_type')
    

class PatientUserSerializer(serializers.ModelSerializer):
    
    patient_user=PatientSerializer(read_only=True)

    class Meta:
        model = User
        exclude = ('password','is_id_verified', 'is_email_verified', 'is_staff', 'is_superuser', 'user_type')
          
        

class AdminDocUpdateSerializer(serializers.ModelSerializer):
    user=DOCUserSerializer()
    class Meta:
        model = Doctor
        fields='__all__' 
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {}) # this is used to pop out the user object and if it is not existing then we will assign a {} to it as default
        user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        return super().update(instance, validated_data)



class AdminClientUpdateSerializer(serializers.ModelSerializer):
    user=DOCUserSerializer()
    class Meta:
        model = Patient
        fields='__all__'

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {}) # this is used to pop out the user object and if it is not existing then we will assign a {} to it as default
        user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        return super().update(instance, validated_data)




# verification serializer


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = '__all__'            




class adminDocVerificationSerializer(serializers.ModelSerializer):
    user=DOCUserSerializer()
    class Meta:
        model = Verification
        fields='__all__'

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {}) # this is used to pop out the user object and if it is not existing then we will assign a {} to it as default
        user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        return super().update(instance, validated_data)
    



class WalletUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        exclude = ['patient'] 





class PatientCustomIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['custom_id']    


class DoctorCustomIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['custom_id']       
        
        
class UserPatientCustomIDSerializer(serializers.ModelSerializer):
    patient_user=PatientCustomIDSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id','first_name','patient_user']

class UserDoctorCustomIDSerializer(serializers.ModelSerializer):
    doctor_user=DoctorCustomIDSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id','first_name','doctor_user']     




class DoctorRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['rating']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['rating']                  
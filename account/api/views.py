import datetime
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from account.models import  Doctor, OTPModel, Patient, Rating, User, Verification, Wallet
from .serializers import  AdminClientUpdateSerializer, AdminDocUpdateSerializer, DoctorRatingSerializer, PatientSerializer, PatientUserSerializer, UserDetailsUpdateSerializer, UserDoctorCustomIDSerializer, UserPatientCustomIDSerializer, UserRegisterSerializer, UserSerializer, VerificationSerializer, WalletUpdateSerializer, adminDocVerificationSerializer
from django.contrib.auth import authenticate
import random
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, ParseError
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from .task import sent_otp
from google.oauth2 import id_token
from google.auth.transport import requests




class generateKey:
    @staticmethod
    def returnValue(email):
        return str(email) + str(timezone.now()) + "Some Random Secret Key"

class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()

            try:
                self.send_otp_email(serializer.data['email'])

            except Exception as e:
                return Response({"Message": "Unknown error", "error": str(e)}, status=500)

        else:
            is_active = False
            content = {
                'message': 'Registration failed',
                'errors': serializer.errors,
                'is_active': is_active
            }
            return Response(content, status=409)

        content = {"Message": "OTP sent successfully",
                   "username": serializer.data['email']
                   }

        return Response(content, status=201)

    def send_otp_email(self, email):
        random_num = random.randint(1000, 9999)
        result = sent_otp.delay(f"{random_num} -OTP", email)
        print(result, '\n\n\n this is the resulet')
        # send_mail(
        #     "OTP AUTHENTICATING Elder Care",
        #     f"{random_num} -OTP",
        #     "ajithajayan222aa@gmail.com",
        #     [email],
        #     fail_silently=False,
        # )

        # Save the generated OTP and timestamp in the database
        otp_model_instance = OTPModel.objects.create(
            user=User.objects.get(email=email),
            otp=random_num,
            timestamp=datetime.now(),
        )
        otp_model_instance.save()

class OTPVerificationView(APIView):
    def post(self, request):
        try:
            user = User.objects.get(email=request.data['email'])
            otp_instance = OTPModel.objects.get(user=user)
        except ObjectDoesNotExist:
            return Response("User does not exist or OTP not generated", status=404)

        if otp_instance.otp == int(request.data['otp']):
            # You can set is_active to True or perform any other necessary actions
            user.is_active = True
            user.save()

            otp_instance.delete()  # Delete the OTP instance after successful verification

            return Response("User successfully verified", status=200)

        return Response("OTP is wrong", status=400)

class ResendOTPView(APIView):
    def post(self, request):
        try:
            user = User.objects.get(email=request.data['email'])
        except ObjectDoesNotExist:
            return Response("User does not exist", status=404)

        # Check if there is an existing OTP instance and resend the OTP
        try:
            otp_instance = OTPModel.objects.get(user=user)
            otp_instance.timestamp = datetime.now()  # Update the timestamp for resend
            otp_instance.save()
        except ObjectDoesNotExist:
            # If OTP instance does not exist, create a new one and send OTP
            register_view = RegisterView()
            register_view.send_otp_email(user.email)

        return Response("OTP resent successfully", status=200)




class UserLogin(APIView):

    def post(self, request):
        print(request.data)
        result = sent_otp.delay("-OTP", 'em23ail@gmail.com')
        print(result, '\n\n\n this is the resulet')
        try:
            email = request.data['email']
            password = request.data['password']
            print(email, password)

        except KeyError:
            raise ParseError('All Fields Are Required')

        if not User.objects.filter(email=email).exists():
            # raise AuthenticationFailed('Invalid Email Address')
            return Response({'detail': 'Email Does Not Exist'}, status=status.HTTP_403_FORBIDDEN)

        if not User.objects.filter(email=email, is_active=True).exists():
            raise AuthenticationFailed(
                'You are blocked by admin ! Please contact admin')

        user = authenticate(username=email, password=password)
        if user is None:
            raise AuthenticationFailed('Invalid Password')

        refresh = RefreshToken.for_user(user)
        print(request.data)

        refresh["first_name"] = str(user.first_name)
        # refresh["is_admin"] = str(user.is_superuser)
        

        content = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'isAdmin': user.is_superuser,
            'is_doctor': user.is_doctor(),
        }
        print(content)
        return Response(content, status=status.HTTP_200_OK)
    

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            print('log out')
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            print("401 error mannnn")
            # return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_401_UNAUTHORIZED)



# class UserDetailsUpdate(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = (MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         user_profile = User.objects.get(id =request.user.id)[0]

     
        
#         user_update_details_serializer = UserDetailsUpdateSerializer(
#             user_profile, data=request.data, partial=True
#         )
        
       
#         if user_update_details_serializer.is_valid():
           
#             user_update_details_serializer.save()
#             return Response(user_update_details_serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             print('error', user_update_details_serializer.errors)
#             return Response(user_update_details_serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
class UserDetailsUpdate(generics.ListAPIView):
    queryset = User.objects.filter(user_type='doctor')
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = UserDetailsUpdateSerializer
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter based on gender
        gender = self.request.query_params.get('gender', None)
        if gender:
            queryset = queryset.filter(gender=gender)

        # Filter based on specialization
        specialization = self.request.query_params.get('specialization', None)
        if specialization:
            queryset = queryset.filter(doctor_user__specializations__icontains=specialization)

        return queryset


    
class PatientUseDetailsUpdate(generics.ListAPIView):
    queryset = User.objects.filter(user_type='client')
    permission_classes = [IsAdminUser]
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = PatientUserSerializer
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']



class DocDetailsUpdate(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = UserDetailsUpdateSerializer
    lookup_field = 'pk'
    

class AdminDocUpdate(generics.RetrieveUpdateAPIView):
    queryset = Doctor.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = AdminDocUpdateSerializer
    lookup_field = 'pk'


class AdminDocDelete(generics.RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'
    

class AdminClientUpdate(generics.RetrieveUpdateAPIView):
    queryset=Patient.objects.all()
    serializer_class = AdminClientUpdateSerializer
    lookup_field = 'pk'
    

class ClientDetailsUpdate(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = PatientUserSerializer
    lookup_field = 'pk'    

class UserDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = User.objects.get(id=request.user.id)
       
        data = UserSerializer(user).data
        try :
            profile_pic = user.profile_picture
            data['profile_pic'] = request.build_absolute_uri('/')[:-1]+profile_pic.url
        except:
            profile_pic = ''
            data['profile_pic']=''
            
        content = data
        return Response(content,status=status.HTTP_200_OK)




class VarificationDoctorView(generics.RetrieveUpdateAPIView):
    serializer_class = VerificationSerializer
    lookup_field = 'user__id'

    def get_queryset(self):
        user_id = self.kwargs.get('user__id')
        user_verification = get_object_or_404(Verification, user__id=user_id)
        return Verification.objects.filter(user=user_verification.user)
    

class AdminDocVerificationView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = adminDocVerificationSerializer
    lookup_field = 'user__id'

    def get_queryset(self):
        user_id = self.kwargs.get('user__id')
        user_verification = get_object_or_404(Verification, user__id=user_id)
        return Verification.objects.filter(user=user_verification.user)
    

class AdminDoctorApprovalListView(generics.ListAPIView):
    queryset = User.objects.filter(
    Q(user_type='doctor') & ~Q(approval_status='APPROVED')  
) 

    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAdminUser]
    serializer_class = UserDetailsUpdateSerializer
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number','approval_status']    



# for to display the wallet amout of the user
    
class WalletAmountView(generics.RetrieveUpdateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletUpdateSerializer
    lookup_field = 'patient_id'



# for getting the cusom id of patient using their user id
    
class PatientCustomIdView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserPatientCustomIDSerializer
    lookup_field = 'pk'    


class DoctorCustomIdView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDoctorCustomIDSerializer
    lookup_field = 'pk' 



#   google authentication 


class UserGoogleAuth(APIView):

    def post(self, request):

        accountExist = True
        GOOGLE_AUTH_API='310720032185-uu1d58btdiim2i6jsq77sblnl99umjo1.apps.googleusercontent.com'
        try:
            google_request = requests.Request()
            id_info = id_token.verify_oauth2_token(
                request.data['client_id'], google_request,  GOOGLE_AUTH_API)
            email = id_info['email']
            print('here is your email from google',email,id_info)



        except KeyError:
            raise ParseError('Check credential')

        if not User.objects.filter(email=email).exists():
            accountExist = False
            username = id_info['name']
            first_name = id_info['given_name']
            last_name = id_info['family_name']
            profile_picture = id_info['picture']

            user = User.objects.create(email=email, first_name=first_name,last_name=last_name,profile_picture=profile_picture,username=username,
                                          is_active=True, is_email_verified=True)
            user.save()
        
        user = User.objects.get(email=email)
        if user.is_active == False:
            return Response({'detail': 'You are blocked by admin ! Please contact admin'}, status=status.HTTP_403_FORBIDDEN)
        elif user.is_doctor():
            return Response({'detail': 'the account is alredy registerd as doctor'}, status=status.HTTP_403_FORBIDDEN)

        else:
            refresh = RefreshToken.for_user(user)
            refresh["is_doctor"] = False
            refresh["first_name"] = str(user.first_name)
            refresh["is_admin"] = False

        content = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'isAdmin': False,
            "isDoctor": False,
            'accountExist': accountExist,
        }
        print(content)

        return Response(content, status=status.HTTP_200_OK)




class DoctorGoogleAuth(APIView):

    def post(self, request):

        accountExist = True
        GOOGLE_AUTH_API='310720032185-uu1d58btdiim2i6jsq77sblnl99umjo1.apps.googleusercontent.com'
        try:
            google_request = requests.Request()
            id_info = id_token.verify_oauth2_token(
                request.data['client_id'], google_request,  GOOGLE_AUTH_API)
            email = id_info['email']
            print('here is your email from google',email,id_info)



        except KeyError:
            raise ParseError('Check credential')

        if not User.objects.filter(email=email).exists():
            accountExist = False
            username = id_info['name']
            first_name = id_info['given_name']
            last_name = id_info['family_name']
            profile_picture = id_info['picture']

            user = User.objects.create(email=email, first_name=first_name,last_name=last_name,profile_picture=profile_picture,username=username,
                                          is_active=True, is_email_verified=True,user_type='doctor')
            user.save()
        
        user = User.objects.get(email=email)
        if user.is_active == False:
            return Response({'detail': 'You are blocked by admin ! Please contact admin'}, status=status.HTTP_403_FORBIDDEN)
        elif not user.is_doctor():
            return Response({'detail': 'the account is alredy registerd as Patient'}, status=status.HTTP_403_FORBIDDEN)

        else:
            refresh = RefreshToken.for_user(user)
            refresh["is_doctor"] = True
            refresh["first_name"] = str(user.first_name)
            refresh["is_admin"] = False

        content = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'isAdmin': False,
            "isDoctor": True,
            'accountExist': accountExist,
        }
        print(content)

        return Response(content, status=status.HTTP_200_OK)


#  for updating the rating of the doctor
    

class DoctorRatingAPIView(generics.RetrieveUpdateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorRatingSerializer

    def get(self, request, *args, **kwargs):
        doctor = self.get_object()
        average_rating = doctor.rating
        return Response({'average_rating': average_rating}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def user_rating_view(request, *args, **kwargs):
    if request.method == 'GET':
        doctor = generics.get_object_or_404(Doctor, pk=kwargs['pk'])
        user = request.user

        try:
            rating = Rating.objects.get(doctor=doctor, user=user).rating
        except Rating.DoesNotExist:
            rating = 0

        return Response({'user_rating': rating}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        rating_value = request.data.get('rating')
        custom_id=request.data.get('custom_id')
        userID=request.data.get('userID')
        user = User.objects.get(id=userID)
        doctor = Doctor.objects.get(custom_id=custom_id)

        try:
            rating_instance = Rating.objects.get(doctor=doctor, user=user)
            rating_instance.rating = rating_value
            rating_instance.save()
        except Rating.DoesNotExist:
            Rating.objects.create(doctor=doctor, user=user, rating=rating_value)

        # After updating the user's rating, recalculate the average rating for the doctor
        doctor.calculate_average_rating()

        return Response({'user_rating': rating_value}, status=status.HTTP_200_OK)
     
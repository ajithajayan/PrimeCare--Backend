# views.py
from xml.dom import ValidationErr
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from notification.models import Notification
from booking.models import DoctorAvailability, Transaction
from .serializers import AdminDocUpdateSerializer, AdminPatientUpdateSerializer, AdvancedSlotUpdateSerializer, DeleteSlotsSerializer, DoctorAvailabilitySerializer, DoctorSlotBulkUpdateSerializer, DoctorSlotUpdateSerializer, RazorpayOrderSerializer, TransactionPatientSerializer, TranscationModelList, TranscationModelSerializer, UserDetailsUpdateSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from account.models import Doctor, Patient, User, Wallet
from django.utils import timezone
from django.utils.timezone import now
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from booking.api.razorpay.main import RazorpayClient
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
channel_layer = get_channel_layer()
from datetime import timedelta,date
from django.db.models import F
# ************************************************************************************************************************************


class DoctorSlotUpdateView(APIView):
    def post(self, request, custom_id):
        try:
            doctor = Doctor.objects.get(custom_id=custom_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorSlotUpdateSerializer(data=request.data, context={'doctor': doctor})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.update_doctor_slots(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationErr as e:
            if 'duplicate_slot' in e.get_codes():
                return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# for creating the slot of a long time period


class DoctorSlotBulkUpdateView(APIView):
    def post(self, request, custom_id):
        try:
            doctor = Doctor.objects.get(custom_id=custom_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorSlotBulkUpdateSerializer(data=request.data, context={'doctor': doctor})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.update_doctor_slots(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            if 'overlap_error' in e.get_codes():
                return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdvancedSlotUpdateView(APIView):
    def post(self, request, custom_id):
        try:
            doctor = Doctor.objects.get(custom_id=custom_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdvancedSlotUpdateSerializer(data=request.data, context={'doctor': doctor})
        try:
            serializer.is_valid(raise_exception=True)
            slots = serializer.update_doctor_slots(doctor)
            return Response({"message": "Slots created successfully", "slots": slots}, status=status.HTTP_200_OK)
        except ValidationError as e:
            if 'overlap_error' in e.get_codes():
                return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)     



class DoctorSlotsAPIView(APIView):
    def get(self, request, custom_id):
        try:
            doctor = Doctor.objects.get(custom_id=custom_id)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

        # Specify the date for which you want to retrieve slots
        date_param = request.query_params.get('date')
        
        if not date_param:
            return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_object = date.fromisoformat(date_param)
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        # Use prefetch_related to optimize the query and fetch availability in a single query
        doctor_with_availability = Doctor.objects.prefetch_related('doctoravailability_set').get(custom_id=custom_id)

        # Retrieve and serialize the available slots for the specified date
        slots = {
            'available_slots': [
                {'from': slot.start_time, 'to': slot.end_time, 'is_booked': slot.is_booked} for slot in doctor_with_availability.doctoravailability_set.filter(day=date_object)
            ]
        }

        return Response(slots, status=status.HTTP_200_OK)

class PatientSlotsCheckingAPIView(APIView):
    def get(self, request, custom_id):
        try:
            doctor = Doctor.objects.get(custom_id=custom_id)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

        # Specify the date for which you want to retrieve slots
        date_param = request.query_params.get('date')
        
        if not date_param:
            return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            requested_date = date.fromisoformat(date_param)
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        # Use prefetch_related to optimize the query and fetch availability in a single query
        doctor_with_availability = Doctor.objects.prefetch_related('doctoravailability_set').get(custom_id=custom_id)

        # Retrieve and serialize the available slots for the specified date
        slots = {
            'available_slots': [
                {'from': slot.start_time, 'to': slot.end_time, 'is_booked': slot.is_booked} for slot in doctor_with_availability.doctoravailability_set.filter(day=requested_date, is_booked=False)
            ]
        }

        return Response(slots, status=status.HTTP_200_OK) 


class DoctorSlotDeleteView(APIView):
    def delete(self, request, custom_id):
        try:
            doctor = Doctor.objects.get(custom_id=custom_id)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        date = request.data.get('date')
        slot = request.data.get('slot')

        try:
            # Assuming DoctorAvailability has a ForeignKey to Doctor named 'doctor'
            doctor_availability = DoctorAvailability.objects.get(doctor=doctor, day=date, start_time=slot['from'], end_time=slot['to'])
            doctor_availability.delete()
            return Response({"message": "Slot deleted successfully"}, status=status.HTTP_200_OK)
        except DoctorAvailability.DoesNotExist:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error deleting slot: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



#****************************************** doctor detail page listing **************************************

class DocDetailList(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = AdminDocUpdateSerializer
    lookup_field = 'pk'

class PatientDetailList(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = AdminPatientUpdateSerializer
    lookup_field = 'pk'




class DoctorsUserSideList(generics.ListAPIView):
    queryset = User.objects.filter(user_type='doctor', approval_status='APPROVED', is_active=True)
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
    




# payment integration for razor pay






rz_client = RazorpayClient()

@api_view(['POST'])
def check_availability(request):
    doctor_id = request.data.get('doctor_id')
    selected_from_time = request.data.get('selected_from_time')
    selected_to_time = request.data.get('selected_to_time')
    selected_day = request.data.get('selected_day')

    doctor_availability = get_object_or_404(DoctorAvailability, doctor_id=doctor_id, day=selected_day, start_time__lte=selected_from_time, end_time__gte=selected_to_time)

    available = not doctor_availability.is_booked

    return Response({'available': available}, status=status.HTTP_200_OK)


class RazorpayOrderAPIView(APIView):
    """This API will create an order"""
    
    def post(self, request):
        razorpay_order_serializer = RazorpayOrderSerializer(
            data=request.data
        )
        if razorpay_order_serializer.is_valid():
            order_response = rz_client.create_order(
                amount=razorpay_order_serializer.validated_data.get("amount"),
                currency=razorpay_order_serializer.validated_data.get("currency")
            )
            response = {
                "status_code": status.HTTP_201_CREATED,
                "message": "order created",
                "data": order_response
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            response = {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "bad request",
                "error": razorpay_order_serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
    

class TransactionAPIView(APIView):
    """This API will complete order and save the 
    transaction"""
    
    def post(self, request):
        transaction_serializer = TranscationModelSerializer(data=request.data)
        if transaction_serializer.is_valid():
            rz_client.verify_payment_signature(
                razorpay_payment_id = transaction_serializer.validated_data.get("payment_id"),
                razorpay_order_id = transaction_serializer.validated_data.get("order_id"),
                razorpay_signature = transaction_serializer.validated_data.get("signature")
            )
            try:
                doctor_id=transaction_serializer.validated_data.get("doctor_id")
                patient_id=transaction_serializer.validated_data.get("patient_id")
                doctor=Doctor.objects.get(custom_id=doctor_id)
                patient=Patient.objects.get(custom_id=patient_id)
                selected_from_time=transaction_serializer.validated_data.get("booked_from_time")
                selected_to_time=transaction_serializer.validated_data.get("booked_to_time")

                selected_day=transaction_serializer.validated_data.get("booked_date")
                
                doctor_availability = get_object_or_404(DoctorAvailability, doctor_id=doctor_id, day=selected_day, start_time__lte=selected_from_time, end_time__gte=selected_to_time)
                doctor_availability.is_booked=True
                doctor_availability.save()
                Notification.objects.create(
            Patient=patient, Doctor=doctor, message=f'{patient.user.first_name} has booked an appointment on {selected_day} @ {selected_from_time}.',
            receiver_type=Notification.RECEIVER_TYPE[1][0],notification_type=Notification.NOTIFICATION_TYPES[0][0]
            )
            except Exception as e:
                print(e)
                return Response({"error": "Doctor availability not found"}, status=status.HTTP_404_NOT_FOUND)

                
            transaction_serializer.save()
            response = {
                "status_code": status.HTTP_201_CREATED,
                "message": "transaction created"
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            response = {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "bad request",
                "error": transaction_serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST) 
        

class PayUsingWalletAPIview(APIView):
    def post(self, request):
        transaction_serializer = TranscationModelSerializer(data=request.data)
        
        if transaction_serializer.is_valid():
            try:
                doctor_id = transaction_serializer.validated_data.get("doctor_id")
                patient_id = transaction_serializer.validated_data.get("patient_id")
                doctor = Doctor.objects.get(custom_id=doctor_id)
                patient = Patient.objects.get(custom_id=patient_id)
                wallet = Wallet.objects.get(patient=patient)

                if wallet.balance >= transaction_serializer.validated_data.get("amount"):
                    wallet.balance -= transaction_serializer.validated_data.get("amount")
                    wallet.save()

                    selected_from_time = transaction_serializer.validated_data.get("booked_from_time")
                    selected_to_time = transaction_serializer.validated_data.get("booked_to_time")
                    selected_day = transaction_serializer.validated_data.get("booked_date")

                    doctor_availability = get_object_or_404(
                        DoctorAvailability,
                        doctor_id=doctor_id,
                        day=selected_day,
                        start_time__lte=selected_from_time,
                        end_time__gte=selected_to_time
                    )
                    doctor_availability.is_booked = True
                    doctor_availability.save()

                    Notification.objects.create(
                        Patient=patient,
                        Doctor=doctor,
                        message=f'{patient.user.first_name} has booked an appointment on {selected_day} @ {selected_from_time}.',
                        receiver_type=Notification.RECEIVER_TYPE[1][0],
                        notification_type=Notification.NOTIFICATION_TYPES[0][0]
                    )

                    transaction_serializer.save()

                    response = {
                        "status_code": status.HTTP_201_CREATED,
                        "message": "Transaction created, and doctor availability updated"
                    }
                    return Response(response, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "Insufficient balance in the wallet"}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                print(e)
                return Response({"error": "Doctor availability not found"}, status=status.HTTP_404_NOT_FOUND)

        else:
            response = {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Bad request",
                "error": transaction_serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def cancel_booking(request):
    transaction_id = request.data.get('transaction_id')
    print("here I got the transaction id", transaction_id)

    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)

        patient_id = transaction.patient_id
        try:
            patient = Patient.objects.get(custom_id=patient_id)
            try:
                wallet = Wallet.objects.get(patient=patient)
                try:
                    doctor = Doctor.objects.get(custom_id=transaction.doctor_id)
                    try:
                        doctor_availability = DoctorAvailability.objects.get(
                            doctor=doctor,
                            day=transaction.booked_date,
                            start_time=transaction.booked_from_time,
                            end_time=transaction.booked_to_time
                        )

                        wallet.balance += (transaction.amount - 50)

                        doctor_availability.is_booked = False
                        doctor_availability.save()
                        wallet.save()
                        transaction.status = 'REFUNDED'
                        transaction.save()
                        Notification.objects.create(
                                Patient=patient,
                                Doctor=doctor,
                                message=f'{patient.user.first_name} has cancelled the appointment on {transaction.booked_date} @ {transaction.booked_from_time}.',
                                receiver_type=Notification.RECEIVER_TYPE[1][0],  # Assuming doctor is the receiver
                                notification_type=Notification.NOTIFICATION_TYPES[3][0]  # 'cancelled'
                        )

                        # # Send notification to the doctor
                        # # channel_layer = get_channel_layer()
                        # doctor_channel_name = f'doctor_{doctor.custom_id}'
                        # notification_message = f"The patient {patient.user.first_name} {patient.user.last_name} has canceled the booking for {transaction.booked_date} from {transaction.booked_from_time} to {transaction.booked_to_time}."
                        # async_to_sync(channel_layer.group_send)(
                        #     doctor_channel_name,
                        #     {
                        #         'type': 'send_notification',
                        #         'message': notification_message,
                        #     }
                        # )

                        return JsonResponse({"message": "Booking canceled successfully"}, status=status.HTTP_200_OK)

                    except DoctorAvailability.DoesNotExist:
                        return JsonResponse({"error": "Doctor availability not found"}, status=status.HTTP_404_NOT_FOUND)

                except Doctor.DoesNotExist:
                    return JsonResponse({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

            except Wallet.DoesNotExist:
                return JsonResponse({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

        except Patient.DoesNotExist:
            return JsonResponse({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
def cancel_booking_doctor(request):
    transaction_id = request.data.get('transaction_id')
    print("here i got the transaction id", transaction_id)

    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)

        patient_id = transaction.patient_id
        try:
            patient = Patient.objects.get(custom_id=patient_id)
            try:
                wallet = Wallet.objects.get(patient=patient)
                try:
                    doctor = Doctor.objects.get(custom_id=transaction.doctor_id)
                    try:
                        doctor_availability = DoctorAvailability.objects.get(
                            doctor=doctor,
                            day=transaction.booked_date,
                            start_time=transaction.booked_from_time,
                            end_time=transaction.booked_to_time
                        )

                        wallet.balance += (transaction.amount)

                       
                        doctor_availability.delete()
                        wallet.save()
                        transaction.status = 'REFUNDED'
                        transaction.save()
                        
                        return JsonResponse({"message": "Booking cancelled successfully"}, status=status.HTTP_200_OK)

                    except DoctorAvailability.DoesNotExist:
                        return JsonResponse({"error": "Doctor availability not found"}, status=status.HTTP_404_NOT_FOUND)

                except Doctor.DoesNotExist:
                    return JsonResponse({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

            except Wallet.DoesNotExist:
                return JsonResponse({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

        except Patient.DoesNotExist:
            return JsonResponse({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)


class TrasactionListAPIView(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TranscationModelList
    pagination_class = PageNumberPagination    
    filter_backends = [SearchFilter]
    permission_classes=[IsAdminUser]
    search_fields = ['transaction_id', 'doctor_id','patient_id', 'booked_date']


class TrasactionRetriveAPIView(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TranscationModelList
    lookup_field = 'pk'


@api_view(['GET'])
def PatientBookingDetailsAPIView(request, patient_id):
    try:
        transactions = Transaction.objects.filter(patient_id=patient_id)
        serializer = TranscationModelList(transactions, many=True)
        response = {
                "status_code": status.HTTP_200_OK,
                "data": serializer.data
            }
        return Response(response, status=status.HTTP_200_OK)
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
def DoctorBookingDetailsAPIView(request, doctor_id):
    try:
        transactions = Transaction.objects.filter(doctor_id=doctor_id)
        serializer = TranscationModelList(transactions, many=True)
        response = {
                "status_code": status.HTTP_200_OK,
                "data": serializer.data
            }
        return Response(response, status=status.HTTP_200_OK)
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
    


from django.http import Http404

class DoctorTransactionsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        doctor_id = request.query_params.get('doctor_id', None)

        if not doctor_id:
            return Response({'error': 'Doctor ID is required in query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = Doctor.objects.get(custom_id=doctor_id)
        except (Doctor.DoesNotExist, ValueError):
            raise Http404("Doctor not found or invalid ID")

        transactions = Transaction.objects.filter(doctor_id=doctor_id, status='COMPLETED')

        processed_patient_ids = set()
        data = []

        for transaction in transactions:
            # Check if the patient ID has been processed before
            if transaction.patient_id in processed_patient_ids:
                continue

            patient = Patient.objects.get(custom_id=transaction.patient_id)
            transaction_data = {
                "transaction_id": transaction.transaction_id,
                "payment_id": transaction.payment_id,
                "order_id": transaction.order_id,
                "signature": transaction.signature,
                "amount": transaction.amount,
                "doctor_id": transaction.doctor_id,
                "patient_id": transaction.patient_id,
                "patient_name": patient.user.first_name,
                "patient_profile_picture": (
                    request.build_absolute_uri('/')[:-1] + patient.user.profile_picture.url
                ) if patient.user.profile_picture else None,
                "booked_date": transaction.booked_date,
                "booked_from_time": transaction.booked_from_time,
                "booked_to_time": transaction.booked_to_time,
                "status": transaction.status,
                "created_at": transaction.created_at,
            }

            processed_patient_ids.add(transaction.patient_id)
            data.append(transaction_data)

        return Response(data, status=status.HTTP_200_OK)






class PatientTransactionsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        patient_id = request.query_params.get('patient_id', None)

        if not patient_id:
            return Response({'error': 'Patient ID is required in query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(custom_id=patient_id)
        except (Patient.DoesNotExist, ValueError):
            raise Http404("Patient not found or invalid ID")

        transactions = Transaction.objects.filter(patient_id=patient_id, status='COMPLETED')

        processed_doctor_ids = set()
        data = []

        for transaction in transactions:
            # Check if the doctor ID has been processed before
            if transaction.doctor_id in processed_doctor_ids:
                continue

            doctor = Doctor.objects.get(custom_id=transaction.doctor_id)
            transaction_data = {
                "transaction_id": transaction.transaction_id,
                "payment_id": transaction.payment_id,
                "order_id": transaction.order_id,
                "signature": transaction.signature,
                "amount": transaction.amount,
                "doctor_id": transaction.doctor_id,
                "patient_id": transaction.patient_id,
                "doctor_name": doctor.user.first_name,
                "doctor_profile_picture": (
                    request.build_absolute_uri('/')[:-1] + doctor.user.profile_picture.url
                ) if doctor.user.profile_picture else "",
                "booked_date": transaction.booked_date,
                "booked_from_time": transaction.booked_from_time,
                "booked_to_time": transaction.booked_to_time,
                "status": transaction.status,
                "created_at": transaction.created_at,
            }

            processed_doctor_ids.add(transaction.doctor_id)
            data.append(transaction_data)

        return Response(data, status=status.HTTP_200_OK)
    
# *****************************************Docotr leave Api View**************************************************
    

from datetime import datetime

class DoctorLeaveUpdateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        doctor_id = request.data.get('custom_id')
        from_date_str = request.data.get('fromDate')
        to_date_str = request.data.get('toDate')

        try:
            doctor = Doctor.objects.get(custom_id=doctor_id)

            # Convert string dates to datetime objects
            from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
            to_date = datetime.strptime(to_date_str, "%Y-%m-%d")

            # Fetch all doctor availability instances within the given date range
            doctor_availability = DoctorAvailability.objects.filter(
                doctor=doctor,
                day__range=(from_date, to_date)
            )

            for slot in doctor_availability:
                if slot.is_booked:
                    try:
                        transaction = Transaction.objects.get(
                            doctor_id=doctor_id,
                            booked_date=slot.day,
                            booked_from_time=slot.start_time,
                            booked_to_time=slot.end_time
                        )

                        try:
                            patient = Patient.objects.get(custom_id=transaction.patient_id)
                            patient_wallet = Wallet.objects.get(patient=patient)
                            patient_wallet.balance = F('balance') + transaction.amount
                            patient_wallet.save()

                            transaction.status = 'REFUNDED'
                            transaction.save()

                            # Use F() expression for atomic update without the need for fetch
                            DoctorAvailability.objects.filter(id=slot.id, is_booked=True).update(is_booked=False)
                            slot.delete()

                        except Patient.DoesNotExist:
                            return JsonResponse({"error": f"Patient not found for transaction {transaction.id}"}, status=status.HTTP_404_NOT_FOUND)
                    except Transaction.DoesNotExist:
                        # Handle if the transaction is not found
                        pass
                else:
                    # If the slot is not booked, delete it
                    slot.delete()

                # Increment the date for the next iteration
                from_date += timedelta(days=1)

        except Doctor.DoesNotExist:
            return JsonResponse({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        return JsonResponse({"message": "Leave applied successfully"}, status=status.HTTP_200_OK)
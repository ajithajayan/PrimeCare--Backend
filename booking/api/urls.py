from django.urls import path
from .views import  AdminDashboardDataAPIView, AdvancedSlotUpdateView, DoctorBookingDetailsAPIView, DoctorSlotBulkUpdateView, DoctorSlotUpdateView,DoctorSlotsAPIView,DoctorSlotDeleteView,DocDetailList, DoctorTransactionsAPIView,DoctorsUserSideList, PatientBookingDetailsAPIView, PatientDetailList, PatientSlotsCheckingAPIView, PatientTransactionsAPIView, PayUsingWalletAPIview,RazorpayOrderAPIView, TrasactionListAPIView, TrasactionRetriveAPIView, cancel_booking, cancel_booking_doctor,check_availability,TransactionAPIView,DoctorLeaveUpdateAPIView    

urlpatterns = [
    path('doctors/<str:custom_id>/slots/', DoctorSlotsAPIView.as_view(), name='doctor-slots-api'),

    # for to check the docotr details from the patient side
    path('patient/check/doctor/<str:custom_id>/slots/', PatientSlotsCheckingAPIView.as_view(), name='doctor-slots-api'),
    
    path('doctors/<str:custom_id>/update_slots/', DoctorSlotUpdateView.as_view(), name='update-doctor-slots'),

    # slot updation for a bulk data
    path('doctors/<str:custom_id>/update_slots/bulk/', DoctorSlotBulkUpdateView.as_view(), name='update-doctor-slots-bulk'),

    # Advanvanced slot creation from the doctor side
    path('doctors/<str:custom_id>/update_slots/advanced/', AdvancedSlotUpdateView.as_view(), name='update-doctor-advacedSlot'),

    path('doctors/<str:custom_id>/delete_slot/', DoctorSlotDeleteView.as_view(), name='delete-slot'),

    # apply leave for the doctor for the selected time period

    path('doctors/<str:custom_id>/update_leave/',DoctorLeaveUpdateAPIView.as_view(),name='doctorLeave-update'),

    #  to get the single Doctor details based on the custom id
    path("detail/doctors/<str:pk>", DocDetailList().as_view(), name="Doc-list"),

    #  to get the single Patient details based on the custom id
    path("detail/patient/<str:pk>", PatientDetailList().as_view(), name="Doc-list"),



    path("doctors/listing/", DoctorsUserSideList.as_view(), name="doctors-listing"),

    # for booking the slots of the doctor

    path('check-availability/', check_availability, name='check-availability'),

    path('create-order/', RazorpayOrderAPIView.as_view(), name='create_order'),

    path('complete-order/', TransactionAPIView.as_view(), name='complete_order'),

    path('detail/transaction/list/', TrasactionListAPIView.as_view(), name='doctor-slots-api'),

    path('detail/transaction/<str:pk>', TrasactionRetriveAPIView.as_view(), name='doctor-slots-api'),


    # pay using wallet

    path('wallet/payment/', PayUsingWalletAPIview.as_view(), name='wallet_order-payment'),

    # for cancel the booking from the patient side

    path('cancel/booking/', cancel_booking, name='cancel-booking'),
    
    # for cancel the booking from the Docotr side

    path('cancel/booking/doctor/', cancel_booking_doctor, name='cancel-booking'),



    # for getting the booking details for the perticular patient for Patient side listing

    path('booking/details/patient/<str:patient_id>', PatientBookingDetailsAPIView, name='booking-details'),

    # for getting the booking details for the perticular Doctor for docotr side listing

    path('booking/details/doctor/<str:doctor_id>', DoctorBookingDetailsAPIView, name='booking-details'),


    # for getting the boking details with patient profile and name

    path('api/doctor-transactions/', DoctorTransactionsAPIView.as_view(), name='doctor-transactions'),
    
    # for getting the boking details with doctor profile and name

    path('api/patient-transactions/', PatientTransactionsAPIView.as_view(), name='patient-transactions'),

    # for getting the details in the admin dashboard

    path('api/admin-transactions/', AdminDashboardDataAPIView.as_view(), name='admin-transactions'),


]
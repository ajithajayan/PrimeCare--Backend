"""
URL configuration for Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static


from booking.consumers import DoctorConsumer
from chat.consumers import ChatConsumer
from notification.consumers import NotificationConsumer


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include("account.api.urls")),
    path('appointment/', include("booking.api.urls")),
    path('chat/', include("chat.api.urls")),
    path('notification/', include("notification.api.urls")),
    

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)







websocket_urlpatterns = [
    path('ws/chat/<int:appointment_id>/', ChatConsumer.as_asgi()),
     path('ws/doctor-notification/<str:custom_id>/', NotificationConsumer.as_asgi()),
]
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterVisitorView.as_view(), name='register-visitor' ),

    path('', views.VisitorView.as_view(), name='get-visitor' ),
    path('<int:pk>', views.UpdateVisitorView.as_view(), name='update-visitor' ),

    path('appointment/', views.YourAppointmentView.as_view(), name='get-appointment' ),
    path('appointment/<int:pk>', views.UpdateYourAppointmentView.as_view(), name='update-appointment' ),
]
from django.urls import path

from .views import ActivateUser, LoginView, LogoutView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('activate/<slug:uidb64>/<slug:token>',ActivateUser.as_view(),name="activate_user"),
]

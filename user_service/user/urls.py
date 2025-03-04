from django.urls import path
from user.views import LoginView, ProviderCreate, BlacklistRefreshView, ValidateTokenAPIView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('signup/', ProviderCreate.as_view()),
    path('logout/', BlacklistRefreshView.as_view()),
    path('auth/validate/', ValidateTokenAPIView.as_view()),
]

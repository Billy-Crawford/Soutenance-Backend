# core/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, ContractViewSet, PaymentViewSet, MessageViewSet, RegisterAdminView, \
    CreateLocataireView, LocataireViewSet, MeViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'profil', MeViewSet, basename='profil')
router.register(r'logements', PropertyViewSet)
router.register(r'contrats', ContractViewSet)
router.register(r'paiements', PaymentViewSet)
router.register(r'messages', MessageViewSet, basename='messages')  # ✅
router.register('locataires', LocataireViewSet, basename='locataires')


urlpatterns = [
    path('', include(router.urls)),

    # Authentification JWT
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register-admin/', RegisterAdminView.as_view(), name='register-admin'),
    path('create-locataire/', CreateLocataireView.as_view(), name='create-locataire'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

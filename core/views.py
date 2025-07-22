import os
from django.db.models import Q
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from config import settings
from utils.email_utils import envoyer_recu_par_mail
from utils.pdf_generator import generer_recu_paiement
from . import models
from .models import Property, Contract, Payment, Message, CustomUser
from .serializers import PropertySerializer, ContractSerializer, PaymentSerializer, MessageSerializer, \
    RegisterAdminSerializer, CreateLocataireSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Contract.objects.all()
        return Contract.objects.filter(locataire=user)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Payment.objects.all()
        return Payment.objects.filter(locataire=user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        paiement = self.get_object()

        if paiement.est_valide:
            return Response({'message': 'Paiement déjà validé'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paiement.est_valide = True

            chemin_relatif = generer_recu_paiement(paiement, request.user.get_full_name())
            paiement.fichier_recu = chemin_relatif
            paiement.save()

            # Chemin absolu du PDF pour l’envoi mail
            chemin_absolu = os.path.join(settings.MEDIA_ROOT, chemin_relatif)

            # Envoi mail
            envoyer_recu_par_mail(paiement, chemin_absolu)

            return Response({
                'message': 'Paiement validé, reçu généré et envoyé par mail.',
                'recu': paiement.fichier_recu.url if paiement.fichier_recu else chemin_relatif
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("Erreur génération reçu ou envoi mail :", e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Messages où l'utilisateur est expéditeur ou destinataire
        return Message.objects.filter(Q(expediteur=user) | Q(destinataire=user))

    def perform_create(self, serializer):
        serializer.save(expediteur=self.request.user)


class RegisterAdminView(generics.CreateAPIView):
    serializer_class = RegisterAdminSerializer
    permission_classes = [AllowAny]  # Tout le monde peut s’inscrire


class IsAdminUserCustom(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class CreateLocataireView(generics.CreateAPIView):
    serializer_class = CreateLocataireSerializer
    permission_classes = [IsAdminUserCustom]


class LocataireViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CreateLocataireSerializer
    permission_classes = [IsAdminUserCustom]

    def get_queryset(self):
        return CustomUser.objects.filter(role='locataire')


class IsLocataire(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'locataire'


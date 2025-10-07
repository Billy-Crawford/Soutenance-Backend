#core/views.py

import os

from django.core.files.base import ContentFile
from django.db.models import Q
from django.http.multipartparser import MultiPartParser
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.parsers import FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from config import settings
from utils.email_utils import envoyer_recu_par_mail
from utils.pdf_generator import generer_recu_paiement
from . import models
from .models import Property, Contract, Payment, Message, CustomUser
from .serializers import PropertySerializer, ContractSerializer, PaymentSerializer, MessageSerializer, \
    RegisterAdminSerializer, CreateLocataireSerializer, LocataireListSerializer, LocataireUpdateSerializer, \
    PropertyCreateSerializer, ProfileSerializer, PasswordChangeSerializer


from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ProfileSerializer, PasswordChangeSerializer



class MeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = ProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        serializer = ProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['password'])
            request.user.save()
            return Response({"detail": "Mot de passe mis à jour avec succès."})
        return Response(serializer.errors, status=400)


class MeFlutterViewSet(viewsets.GenericViewSet):
    """
       Vue spécifique pour Flutter :
       - GET  -> Récupérer le profil
       - PATCH -> Mettre à jour le profil (y compris photo)
       """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_object(self):
        # On retourne toujours l'utilisateur connexte
        return self.request.user



class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PropertyCreateSerializer
        return PropertySerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Property.objects.filter(proprietaire=user)
        # Pour les locataires : retourne les logements liés à leurs contrats
        return Property.objects.filter(contract__locataire=user).distinct()


# class ContractViewSet(viewsets.ModelViewSet):
#     queryset = Contract.objects.all()
#     serializer_class = ContractSerializer
#     permission_classes = [IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#         if user.role == 'admin':
#             return Contract.objects.filter(logement__proprietaire=user)
#         return Contract.objects.filter(locataire=user)

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Contract.objects.filter(logement__proprietaire=user)
        return Contract.objects.filter(locataire=user)

    def perform_create(self, serializer):
        """
        Surcharge pour s'assurer que le fichier PDF est bien stocké dans Cloudinary
        au lieu d'un stockage local.
        """
        contract = serializer.save()
        if contract.fichier_pdf:
            # ✅ Cloudinary gère automatiquement le stockage
            # donc on n'a pas besoin d'utiliser .path ni de manipuler un fichier local
            contract.fichier_pdf.url  # forcer l'URL Cloudinary
        return contract

    def perform_update(self, serializer):
        """
        Même logique lors d'une mise à jour : toujours s'assurer que l'URL Cloudinary est utilisée.
        """
        contract = serializer.save()
        if contract.fichier_pdf:
            contract.fichier_pdf.url
        return contract

# class PaymentViewSet(viewsets.ModelViewSet):
#     queryset = Payment.objects.all()
#     serializer_class = PaymentSerializer
#     permission_classes = [IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#         if user.role == "admin":
#             return Payment.objects.filter(logement__proprietaire=user)
#         return Payment.objects.filter(locataire=user)
#
#     def perform_create(self, serializer):
#         # Injecte automatiquement le locataire connecté lors de la création
#         serializer.save(locataire=self.request.user)
#
#     @action(detail=False, methods=["get"])
#     def mes_paiements(self, request):
#         user = request.user
#         paiements = Payment.objects.filter(locataire=user).order_by("-date_paiement")
#         serializer = self.get_serializer(
#             paiements, many=True, context={"request": request}
#         )
#         return Response(serializer.data)
#
#     @action(detail=True, methods=["post"])
#     def valider(self, request, pk=None):
#         paiement = self.get_object()
#
#         if paiement.est_valide:
#             return Response(
#                 {"message": "Paiement déjà validé"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         try:
#             paiement.est_valide = True
#
#             # Génère le reçu PDF en mémoire (bytes)
#             pdf_bytes = generer_recu_paiement(paiement, request.user.get_full_name())
#
#             # ✅ Sauvegarde directement dans Cloudinary via FileField
#             paiement.fichier_recu.save(
#                 f"recu_paiement_{paiement.id}.pdf",
#                 ContentFile(pdf_bytes),
#                 save=True
#             )
#
#             # Envoi mail avec le lien Cloudinary
#             if paiement.fichier_recu:
#                 envoyer_recu_par_mail(paiement, paiement.fichier_recu.url)
#
#             return Response(
#                 {
#                     "message": "Paiement validé, reçu généré avec succès",
#                     "recu": paiement.fichier_recu.url if paiement.fichier_recu else None,
#                 },
#                 status=status.HTTP_200_OK,
#             )
#
#         except Exception as e:
#             print("Erreur génération reçu ou envoi mail :", e)
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from .models import Payment
from .serializers import PaymentSerializer
from utils.pdf_generator import generer_recu_paiement
from utils.mail_utils import envoyer_recu_par_mail  # si tu as cette fonction

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        # ✅ Important pour permettre au serializer d'accéder à la requête
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Payment.objects.filter(logement__proprietaire=user)
        return Payment.objects.filter(locataire=user)

    def perform_create(self, serializer):
        serializer.save(locataire=self.request.user)

    @action(detail=False, methods=["get"])
    def mes_paiements(self, request):
        user = request.user
        paiements = Payment.objects.filter(locataire=user).order_by("-date_paiement")
        serializer = self.get_serializer(paiements, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        paiement = self.get_object()

        if paiement.est_valide:
            return Response(
                {"message": "Paiement déjà validé"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            paiement.est_valide = True

            # ✅ Génération correcte du fichier PDF
            recu_pdf = generer_recu_paiement(
                paiement,
                request.user.get_full_name() or request.user.username
            )

            # ✅ Sauvegarde correcte sur Cloudinary ou MEDIA_ROOT
            paiement.fichier_recu.save(recu_pdf.name, recu_pdf, save=True)
            paiement.save()

            # ✅ Envoi du reçu par mail (optionnel)
            if paiement.fichier_recu:
                try:
                    envoyer_recu_par_mail(paiement, paiement.fichier_recu.url)
                except Exception as mail_err:
                    print("Erreur d’envoi du mail :", mail_err)

            return Response(
                {
                    "message": "Paiement validé et reçu généré avec succès",
                    "recu": paiement.fichier_recu.url if paiement.fichier_recu else None,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print("Erreur lors de la validation du paiement :", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(expediteur=user) | Q(destinataire=user))

    def perform_create(self, serializer):
        serializer.save(expediteur=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.expediteur != request.user:
            return Response(
                {'detail': "Vous ne pouvez supprimer que vos propres messages."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='conversation/(?P<user_id>[^/.]+)')
    def conversation(self, request, user_id=None):
        user = request.user
        try:
            destinataire = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=404)

        messages = Message.objects.filter(
            Q(expediteur=user, destinataire=destinataire) |
            Q(expediteur=destinataire, destinataire=user)
        ).order_by('date_envoi')

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)



class RegisterAdminView(generics.CreateAPIView):
    serializer_class = RegisterAdminSerializer
    permission_classes = [AllowAny]  # Tout le monde peut s’inscrire


class IsAdminUserCustom(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class CreateLocataireView(generics.CreateAPIView):
    serializer_class = CreateLocataireSerializer
    permission_classes = [IsAdminUserCustom]


class LocataireViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserCustom]

    def get_queryset(self):
        user = self.request.user
        return CustomUser.objects.filter(role='locataire', proprietaire=user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'create']:
            return LocataireUpdateSerializer
        return LocataireListSerializer


class IsLocataire(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'locataire'


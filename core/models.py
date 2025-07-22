# core/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('locataire', 'Locataire'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES,default='locataire')

    def __str__(self):
        return f"{self.username} ({self.role}"

LOGEMENT_TYPES = [
    ('chambre', 'Chambre simple'),
    ('studio', 'Studio'),
    ('chambresalon', 'Chambre-salon'),
    ('appartement', 'Appartement'),
    ('villa', 'Villa'),
    ('bureau', 'Bureau'),
    ('boutique', 'Boutique'),
]

class Property(models.Model):
    nom = models.CharField(max_length=100)
    type_logement = models.CharField(max_length=20, choices=LOGEMENT_TYPES)
    adresse = models.TextField()
    description = models.TextField(blank=True)
    loyer_mensuel = models.DecimalField(max_digits=10, decimal_places=2)
    caution = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_mois = models.PositiveIntegerField()
    images = models.JSONField(default=list, blank=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} - {self.type_logement}"


class Contract(models.Model):
    locataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'locataire'})
    logement = models.ForeignKey(Property, on_delete=models.CASCADE)
    fichier_pdf = models.FileField(upload_to='contrats/')
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrat {self.locataire.username} - {self.logement.nom}"


PAYMENT_TYPES = [
    ('loyer', 'Loyer'),
    ('eau', 'Eau'),
    ('electricite', 'Électricité'),
    ('internet', 'Internet'),
    ('reparation', 'Réparation'),
]

class Payment(models.Model):
    locataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'locataire'})
    logement = models.ForeignKey(Property, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    type_paiement = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    mois_concerne = models.CharField(max_length=20, help_text="Ex: Juin 2025")
    est_valide = models.BooleanField(default=False)
    date_paiement = models.DateTimeField(default=timezone.now)
    fichier_recu = models.FileField(upload_to='recus/', blank=True, null=True)

    def __str__(self):
        return f"{self.locataire.username} - {self.type_paiement} - {self.mois_concerne}"

class Message(models.Model):
    expediteur = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='messages_envoyes', on_delete=models.CASCADE)
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='messages_recus', on_delete=models.CASCADE)
    texte = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_envoi']

    def __str__(self):
        return f"Message de {self.expediteur} à {self.destinataire} - {self.date_envoi.strftime('%Y-%m-%d %H:%M')}"

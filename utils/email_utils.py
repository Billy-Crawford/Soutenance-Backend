from django.core.mail import EmailMessage
from django.conf import settings
import os

def envoyer_recu_par_mail(paiement, chemin_recu_absolu):
    sujet = f"Reçu de paiement n°{paiement.id}"
    message = f"Bonjour {paiement.locataire.first_name},\n\nVoici le reçu de votre paiement."
    destinataire = [paiement.locataire.email]

    email = EmailMessage(
        sujet,
        message,
        settings.DEFAULT_FROM_EMAIL,
        destinataire,
    )

    if os.path.exists(chemin_recu_absolu):
        email.attach_file(chemin_recu_absolu)

    email.send(fail_silently=False)

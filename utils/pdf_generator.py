from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from django.conf import settings
from datetime import datetime

def generer_recu_paiement(paiement, admin_nom):
    # Nom fichier
    filename = f"recu_paiement_{paiement.id}.pdf"

    # Chemin absolu complet
    dir_recus = os.path.join(settings.MEDIA_ROOT, "recus")
    os.makedirs(dir_recus, exist_ok=True)
    path_absolu = os.path.join(dir_recus, filename)

    # Création PDF
    c = canvas.Canvas(path_absolu, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "REÇU DE PAIEMENT")

    c.setFont("Helvetica", 12)
    c.drawString(100, 770, f"Locataire : {paiement.locataire.get_full_name() or paiement.locataire.username}")
    c.drawString(100, 750, f"Montant payé : {paiement.montant} FCFA")
    c.drawString(100, 730, f"Mois concerné : {paiement.mois_concerne}")
    c.drawString(100, 710, f"Type de paiement : {paiement.get_type_paiement_display()}")
    c.drawString(100, 690, f"Date de paiement : {paiement.date_paiement.strftime('%d/%m/%Y à %H:%M')}")
    c.drawString(100, 670, f"Logement ID : {paiement.logement.id}")
    c.drawString(100, 650, f"Validé par : {admin_nom}")
    c.drawString(100, 630, f"Date génération : {datetime.now().strftime('%d/%m/%Y')}")

    c.save()

    # Retourner chemin relatif compatible FileField (ex: 'recus/recu_paiement_1.pdf')
    return f"recus/{filename}"

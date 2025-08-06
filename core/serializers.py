from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.templatetags.rest_framework import data
from .models import Property, Contract, Payment, Message, CustomUser, ImageLogement
from utils.pdf_generator import generer_recu_paiement


class ImageLogementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageLogement
        fields = ['id', 'image']

class PropertyCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Property
        fields = [
            'nom', 'type_logement', 'adresse', 'description',
            'loyer_mensuel', 'caution', 'minimum_mois', 'images'
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        proprietaire = self.context['request'].user
        property_instance = Property.objects.create(proprietaire=proprietaire, **validated_data)

        for image in images_data:
            ImageLogement.objects.create(logement=property_instance, image=image)

        return property_instance


class PropertySerializer(serializers.ModelSerializer):
    images = ImageLogementSerializer(many=True, read_only=True)
    est_loue = serializers.SerializerMethodField()
    contrat_pdf_url = serializers.SerializerMethodField()  # Nouveau champ

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['proprietaire']

    def get_est_loue(self, obj):
        return obj.contract_set.exists()

    def get_contrat_pdf_url(self, obj):
        contract = obj.contract_set.first()  # Prend le premier contrat trouvé
        if contract and contract.fichier_pdf:
            return self.context['request'].build_absolute_uri(contract.fichier_pdf.url)
        return None


class ContractSerializer(serializers.ModelSerializer):
    locataire_display = serializers.SerializerMethodField(read_only=True)
    logement_detail = PropertySerializer(source='logement', read_only=True)  # 🔥 Nouveau champ détaillé

    class Meta:
        model = Contract
        fields = [
            'id',
            'locataire',
            'logement',
            'fichier_pdf',
            'date_debut',
            'date_fin',
            'date_creation',
            'locataire_display',
            'logement_detail',  # ✅ à la place de logement_display
        ]
        extra_kwargs = {
            'locataire': {'required': True},
            'logement': {'required': True},
        }

    def validate(self, data):
        date_debut = data.get("date_debut")
        date_fin = data.get("date_fin")
        if date_debut and date_fin and date_fin <= date_debut:
            raise serializers.ValidationError("La date de fin doit être postérieure à la date de début.")
        return data

    def get_locataire_display(self, obj):
        return f"{obj.locataire.first_name} {obj.locataire.last_name}".strip() or obj.locataire.username


class PaymentSerializer(serializers.ModelSerializer):
    fichier_recu_url = serializers.SerializerMethodField()
    locataire_nom = serializers.SerializerMethodField()
    proprietaire_nom = serializers.SerializerMethodField()
    logement_nom = serializers.CharField(source="logement.nom", read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'logement',
            'locataire_nom', 'proprietaire_nom', 'logement_nom',
            'montant', 'type_paiement', 'mode_paiement',
            'mois_concerne', 'est_valide',
            'date_paiement', 'fichier_recu_url', 'fichier_recu'
        ]

    def get_fichier_recu_url(self, obj):
        request = self.context.get('request')
        if obj.fichier_recu and request:
            return request.build_absolute_uri(obj.fichier_recu.url)
        return None

    def get_locataire_nom(self, obj):
        return f"{obj.locataire.first_name} {obj.locataire.last_name}".strip() or obj.locataire.username

    def get_proprietaire_nom(self, obj):
        return obj.logement.proprietaire.get_full_name() or obj.logement.proprietaire.username

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        validated_data['locataire'] = user
        return super().create(validated_data)

    # def create(self, validated_data):
    #     return Payment.objects.create(**validated_data)


class MessageSerializer(serializers.ModelSerializer):
    expediteur = serializers.StringRelatedField(read_only=True)  # Affiche username ou __str__
    destinataire = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = Message
        fields = ['id', 'expediteur', 'destinataire', 'texte', 'image', 'date_envoi']
        read_only_fields = ['id', 'expediteur', 'date_envoi']

    def validate(self, data):
        if not data.get('texte') and not data.get('image'):
            raise serializers.ValidationError("Un message doit contenir du texte ou une image.")
        return data


class RegisterAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)  # Confirmation mot de passe

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='admin'  # FORCE le rôle admin
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class CreateLocataireSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)  # Confirmation

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='locataire',
            proprietaire=self.context['request'].user  # 🔥 ajouter le propriétaire ici
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class LocataireListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class LocataireUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

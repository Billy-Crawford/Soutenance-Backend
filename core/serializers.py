from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Property, Contract, Payment, Message, CustomUser
from utils.pdf_generator import generer_recu_paiement

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    fichier_recu_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = '__all__'

    def get_fichier_recu_url(self, obj):
        request = self.context.get('request')
        if obj.fichier_recu and request:
            return request.build_absolute_uri(obj.fichier_recu.url)
        return None

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
            role='locataire'  # rôle locataire
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

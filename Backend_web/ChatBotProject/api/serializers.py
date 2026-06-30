from rest_framework import serializers
from .models import AppUser, Interaction, BotConfig, SystemSettings


# ─── INTERACTION SERIALIZER ──────────────────────────────────────────────────
class InteractionSerializer(serializers.ModelSerializer):
    # Formate la date de manière lisible pour l'application mobile
    date = serializers.SerializerMethodField()

    class Meta:
        model = Interaction
        fields = ['id', 'type_interaction', 'date', 'summary']

    def get_date(self, obj):
        # Retourne un format propre (Ex: "06 Juin, 23:12")
        from django.utils.formats import date_format
        return date_format(obj.date_created, "d N, H:i")


# ─── APP USER SERIALIZER ──────────────────────────────────────────────────────
class AppUserSerializer(serializers.ModelSerializer):
    interactions = InteractionSerializer(many=True, read_only=True)
    totalInteractions = serializers.IntegerField(source='total_interactions', read_only=True)
    joinedDate = serializers.SerializerMethodField()

    class Meta:
        model = AppUser
        fields = ['id', 'name', 'email', 'avatar', 'joinedDate', 'totalInteractions', 'is_blocked', 'interactions', 'note']

    def get_joinedDate(self, obj):
        # Formatage de la date en français pour correspondre au design existant
        months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        if obj.joined_date:
            return f"{obj.joined_date.day:02d} {months[obj.joined_date.month - 1]} {obj.joined_date.year}"
        return ""


# ─── BOT CONFIG SERIALIZER ──────────────────────────────────────────────────
class BotConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotConfig
        fields = ['id', 'bot_name', 'welcome_message', 'selected_color', 'selected_avatar', 'updated_at']
        read_only_fields = ['id', 'updated_at']


# ─── SYSTEM SETTINGS SERIALIZER ─────────────────────────────────────────────
class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = [
            'id', 'user_name', 'user_email', 'selected_language',
            'is_two_factor_auth', 'is_push_notify', 'is_email_notify', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']
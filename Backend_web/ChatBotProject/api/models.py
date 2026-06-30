from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

# ─── CONFIGURATION NY BOT ──────────────────────────────────────────────────────
class BotConfig(models.Model):
    bot_name = models.CharField(max_length=30, default="MadaBot Assistant")
    welcome_message = models.CharField(max_length=160, default="Bonjour ! Je suis votre assistant virtuel. Comment puis-je vous aider aujourd’hui ?")
    selected_color = models.CharField(max_length=7, default="#10B981")  # Hex Color
    selected_avatar = models.CharField(max_length=10, default="🤖")     # Emoji na icon string
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.bot_name


# ─── MODELY CHATBOT ────────────────────────────────────────────────────────────
class Chatbot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbots', null=True, blank=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ─── CONVERSATION SY MESSAGE ───────────────────────────────────────────────────
class Conversation(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("ended", "Ended"),
        ("escalated", "Escalated to human"),
    ]
    
    chatbot = models.ForeignKey('Chatbot', on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    visitor_id = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    converted = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["chatbot", "started_at"]),
        ]

    def __str__(self):
        return f"Conv {self.id} - {self.chatbot.name if self.chatbot else 'Unknown'}"


class Message(models.Model):
    SENDER_CHOICES = [
        ("user", "User"),
        ("bot", "Bot"),
        ("ai", "AI Node"),
        ("agent", "Human Agent"),
    ]
    
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    node_id = models.CharField(max_length=120, blank=True, null=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    ai_tokens_used = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}..."


# ─── MESSAGELOG HO AN'NY DASHBOARD ────────────────────────────────────────────
class MessageLog(models.Model):
    SENDER_CHOICES = [('user', 'User/Visitor'), ('bot', 'Chatbot')]
    chatbot = models.ForeignKey('Chatbot', on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, default='user')
    text = models.TextField(blank=True, default="")
    session_id = models.CharField(max_length=255, blank=True, default="")
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Log {self.id} - {self.sender} at {self.timestamp}"


# ─── CHATMESSAGE (HO AN'NY CHAT HISTORY) ──────────────────────────────────────
class ChatMessage(models.Model):
    sender = models.CharField(max_length=10) 
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:20]}..."


# ─── APPUSER SY INTERACTION ────────────────────────────────────────────────────
class AppUser(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nom complet")
    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    avatar = models.CharField(max_length=10, blank=True, verbose_name="Initiales Avatar")
    joined_date = models.DateField(auto_now_add=True, verbose_name="Date d'adhésion")
    is_blocked = models.BooleanField(default=False, verbose_name="Est bloqué")
    note = models.TextField(blank=True, default="", verbose_name="Note interne")

    class Meta:
        ordering = ['name']
        verbose_name = "Utilisateur de l'application"
        verbose_name_plural = "Utilisateurs de l'application"

    def __str__(self):
        return self.name

    @property
    def total_interactions(self):
        return self.interactions.count()


class Interaction(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='interactions', verbose_name="Utilisateur")
    type_interaction = models.CharField(max_length=50, verbose_name="Type (FAQ, Support, Spam...)")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'interaction")
    summary = models.TextField(verbose_name="Résumé de l'interaction")

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Interaction"
        verbose_name_plural = "Interactions"

    def __str__(self):
        return f"[{self.type_interaction}] {self.user.name} - {self.date_created.strftime('%d/%m/%Y')}"


# ─── SYSTEM SETTINGS ───────────────────────────────────────────────────────────
class SystemSettings(models.Model):
    user_name = models.CharField(max_length=150, default="Fanomezantsoa Rado")
    user_email = models.EmailField(unique=True, default="rado.andrinaivo@email.com")
    selected_language = models.CharField(max_length=50, default="Français")
    is_two_factor_auth = models.BooleanField(default=True)
    is_push_notify = models.BooleanField(default=True)
    is_email_notify = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user_name}"

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"


# ─── DAILY METRIC (HO AN'NY ANALYTICS) ──────────────────────────────────────
class DailyMetric(models.Model):
    chatbot = models.ForeignKey('Chatbot', on_delete=models.CASCADE, related_name="daily_metrics")
    date = models.DateField()
    messages_count = models.PositiveIntegerField(default=0)
    conversations_count = models.PositiveIntegerField(default=0)
    converted_count = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0)
    unique_active_users = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("chatbot", "date")
        indexes = [
            models.Index(fields=["chatbot", "date"]),
        ]

    def __str__(self):
        return f"{self.chatbot.name} - {self.date}"
import os
import re
import requests
import base64
import random
import datetime
import zoneinfo
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.decorators import api_view, parser_classes, action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated

from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth.models import User

from .models import (
    ChatMessage, 
    MessageLog, 
    Chatbot, 
    Conversation, 
    Message,
    AppUser, 
    Interaction, 
    BotConfig, 
    SystemSettings,
    DailyMetric
)
from .serializers import AppUserSerializer, BotConfigSerializer
from .pagination import CustomUserPagination

tz_mada = zoneinfo.ZoneInfo("Indian/Antananarivo")

# URL de l'API Groq
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = os.getenv("GROQ_API_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ════════════════════════════════════════════════════════════════════
# CHAT WITH AI
# ════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def chat_with_ai(request):
    try:
        # 1. Récupération des données
        user_message = request.data.get('message', request.POST.get('message', '')).strip()
        image_file = request.FILES.get('image', None)
        
        session_id = request.data.get('session_id', request.POST.get('session_id', 'session_default'))
        chatbot_id = request.data.get('chatbot_id', request.POST.get('chatbot_id', None))

        print(f"--- DEBUG BACKEND ---")
        print(f"Texte reçu: '{user_message}'")
        print(f"Fichier reçu: {image_file}")
        print(f"Session ID: {session_id}")
        print(f"Chatbot ID: {chatbot_id}")
        print(f"---------------------")

        if not user_message and not image_file:
            return Response(
                {'error': "Le message ou l'image ne peut pas être vide."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 📌 1. MIANToka NY CHATBOT
        if not chatbot_id:
            first_bot = Chatbot.objects.first()
            if not first_bot:
                first_bot = Chatbot.objects.create(name="Default Bot", is_active=True)
            chatbot_id = first_bot.id

        # 📌 2. MIANToka NY CONVERSATION
        conversation, created = Conversation.objects.get_or_create(
            chatbot_id=chatbot_id,
            visitor_id=session_id,
            defaults={
                'status': 'active',
                'converted': False
            }
        )
        
        if created:
            print(f"✅ Nouvelle conversation créée: {conversation.id}")
        else:
            conversation.last_message_at = timezone.now()
            conversation.save()

        # 📌 3. MITAHIRY NY MESSAGE USER AO AMIN'NY MessageLog
        log_message = user_message if user_message else "[Image envoyée]"
        
        MessageLog.objects.create(
            chatbot_id=chatbot_id,
            conversation=conversation,
            sender='user',
            text=log_message,
            session_id=session_id,
            timestamp=timezone.now()
        )

        # 📌 4. MITAHIRY AO AMIN'NY ChatMessage
        ChatMessage.objects.create(sender='user', message=log_message)

        # 5. Préparation pour Groq
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        selected_model = "llama-3.1-8b-instant"
        
        if image_file:
            selected_model = "llama-3.2-11b-vision-preview"
            image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            content_type = image_file.content_type if hasattr(image_file, 'content_type') else "image/jpeg"
            
            final_content = []
            if user_message:
                final_content.append({"type": "text", "text": user_message})
            else:
                final_content.append({"type": "text", "text": "Analyse cette image."})
                
            final_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{content_type};base64,{base64_image}"
                }
            })
        else:
            final_content = user_message if user_message else "Bonjour"

        payload = {
            "model": selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant virtuel de chat. "
                        "Réponds de manière extrêmement concise, directe et en français uniquement. "
                        "Ne commence jamais par des phrases d'introduction robotiques."
                    )
                },
                {
                    "role": "user",
                    "content": final_content
                }
            ],
            "temperature": 0.5
        }

        # 6. Envoi à l'API Groq
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"❌ Erreur Groq: {response.text}")
            return Response({
                'error': "L'API Groq a renvoyé une erreur.",
                'details': response.text
            }, status=status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        ai_response = response_data['choices'][0]['message']['content']

        if "Je suis prêt à aider" in ai_response or "Pour résoudre un problème" in ai_response:
            ai_response = "Bonjour ! En quoi puis-je vous aider aujourd'hui ?"

        # 📌 7. MITAHIRY NY VALIN'NY BOT AO AMIN'NY MessageLog
        MessageLog.objects.create(
            chatbot_id=chatbot_id,
            conversation=conversation,
            sender='bot',
            text=ai_response,
            session_id=session_id,
            timestamp=timezone.now()
        )

        # 📌 8. MITAHIRY AO AMIN'NY ChatMessage
        ChatMessage.objects.create(sender='bot', message=ai_response)

        # 9. Réponse finale
        return Response({'reply': ai_response}, status=status.HTTP_200_OK)

    except KeyError as e:
        print(f"🔑 KeyError: {str(e)}")
        return Response({'error': f"Structure JSON incorrecte: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(f"💥 Erreur inattendue: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ════════════════════════════════════════════════════════════════════
# DASHBOARD ANALYTICS VIEW
# ════════════════════════════════════════════════════════════════════
class DashboardAnalyticsView(APIView):
    """
    API mamerina ny antontan'isa rehetra ilain'ny Dashboard React Native
    """
    def get(self, request, format=None):
        try:
            today = timezone.now().date()
            
            # 1. Total Chatbots
            total_chatbots = Chatbot.objects.count()
            
            # 2. New Chatbots this week
            one_week_ago = timezone.now() - timedelta(days=7)
            new_chatbots_week = Chatbot.objects.filter(created_at__gte=one_week_ago).count()
            
            # 3. Conversations today (sessions uniques)
            conversations_today = MessageLog.objects.filter(
                timestamp__date=today
            ).values('session_id').distinct().count()
            
            # 4. Conversations yesterday
            conversations_yesterday = MessageLog.objects.filter(
                timestamp__date=today - timedelta(days=1)
            ).values('session_id').distinct().count()
            
            # 5. Evolution vs yesterday
            if conversations_yesterday == 0:
                evolution_vs_yesterday = f"▲ +{conversations_today}" if conversations_today > 0 else "0%"
            else:
                pct = int(((conversations_today - conversations_yesterday) / conversations_yesterday) * 100)
                if pct >= 0:
                    evolution_vs_yesterday = f"▲ +{pct}%"
                else:
                    evolution_vs_yesterday = f"▼ {pct}%"
            
            # 6. Active Users (sessions uniques dernières 24h)
            last_24h = timezone.now() - timedelta(hours=24)
            active_users = MessageLog.objects.filter(
                timestamp__gte=last_24h,
                sender='user'
            ).values('session_id').distinct().count()
            
            # 7. Total Messages this month
            total_messages_month_count = MessageLog.objects.filter(
                timestamp__year=today.year,
                timestamp__month=today.month
            ).count()
            
            if total_messages_month_count >= 1000:
                formatted_messages = f"{round(total_messages_month_count / 1000, 1)}K"
            else:
                formatted_messages = str(total_messages_month_count)

            # 8. Weekly Data
            weekly_data = []
            for i in range(6, -1, -1):
                target_date = today - timedelta(days=i)
                day_count = MessageLog.objects.filter(
                    timestamp__date=target_date
                ).count()
                weekly_data.append(day_count)

            response_data = {
                "total_chatbots": total_chatbots,
                "new_chatbots_week": new_chatbots_week,
                "conversations_today": conversations_today,
                "evolution_vs_yesterday": evolution_vs_yesterday,
                "active_users": active_users,
                "total_messages_month": formatted_messages,
                "weekly_data": weekly_data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ════════════════════════════════════════════════════════════════════
# ANALYTICS VIEW HO AN'NY REACT NATIVE
# ════════════════════════════════════════════════════════════════════
class AnalyticsView(APIView):
    """
    API mamerina ny antontan'isa amin'ny endrika ilain'ny React Native AnalyticsScreen
    Endrika: { messages, responseTime, conversionRate, activeUsers }
    """
    
    def get(self, request, format=None):
        try:
            range_key = request.query_params.get('range', '7d')
            
            # Famaritana ny daty
            today = timezone.now().date()
            
            if range_key == 'today':
                start_date = today
                days = 1
            elif range_key == '7d':
                start_date = today - timedelta(days=6)
                days = 7
            elif range_key == '30d':
                start_date = today - timedelta(days=29)
                days = 30
            else:
                start_date = today - timedelta(days=6)
                days = 7
            
            # 1. Messages
            total_messages = MessageLog.objects.filter(
                timestamp__date__gte=start_date,
                timestamp__date__lte=today
            ).count()
            
            daily_messages = []
            for i in range(days):
                target_date = start_date + timedelta(days=i)
                count = MessageLog.objects.filter(
                    timestamp__date=target_date
                ).count()
                daily_messages.append(count)
            
            # Total messages previous period
            prev_start = start_date - timedelta(days=days)
            prev_messages = MessageLog.objects.filter(
                timestamp__date__gte=prev_start,
                timestamp__date__lt=start_date
            ).count()
            
            messages_change = 0
            if prev_messages > 0:
                messages_change = round(((total_messages - prev_messages) / prev_messages) * 100, 1)
            elif total_messages > 0:
                messages_change = 100
            
            # 2. Response Time (simulation)
            response_time_values = []
            for i in range(days):
                response_time_values.append(round(random.uniform(1.2, 4.8), 1))
            
            avg_response_time = round(sum(response_time_values) / len(response_time_values), 1) if response_time_values else 0
            
            # 3. Conversion Rate (simulation)
            conversion_values = []
            for i in range(days):
                conversion_values.append(round(random.uniform(10, 40), 1))
            
            avg_conversion = round(sum(conversion_values) / len(conversion_values), 1) if conversion_values else 0
            
            # 4. Active Users
            active_users = MessageLog.objects.filter(
                timestamp__date__gte=start_date,
                sender='user'
            ).values('session_id').distinct().count()
            
            active_users_values = []
            for i in range(days):
                target_date = start_date + timedelta(days=i)
                count = MessageLog.objects.filter(
                    timestamp__date=target_date,
                    sender='user'
                ).values('session_id').distinct().count()
                active_users_values.append(count)
            
            response_data = {
                "messages": {
                    "total": total_messages,
                    "change": messages_change,
                    "history": daily_messages
                },
                "responseTime": {
                    "total": avg_response_time,
                    "change": 0,
                    "history": response_time_values
                },
                "conversionRate": {
                    "total": avg_conversion,
                    "change": 0,
                    "history": conversion_values
                },
                "activeUsers": {
                    "total": active_users,
                    "change": 0,
                    "history": active_users_values
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ════════════════════════════════════════════════════════════════════
# APP USER VIEWSET
# ════════════════════════════════════════════════════════════════════
class AppUserViewSet(viewsets.ModelViewSet):
    queryset = AppUser.objects.prefetch_related('interactions').all()
    serializer_class = AppUserSerializer
    pagination_class = CustomUserPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query)
            )

        sort_by = self.request.query_params.get('sort_by', 'name_asc')
        if sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'joined_asc':
            queryset = queryset.order_by('joined_date')
        elif sort_by == 'joined_desc':
            queryset = queryset.order_by('-joined_date')

        return queryset

    @action(detail=True, methods=['post'], url_path='toggle-block')
    def toggle_block(self, request, pk=None):
        user = self.get_object()
        user.is_blocked = not user.is_blocked
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='export-interactions')
    def export_interactions(self, request, pk=None):
        user = self.get_object()
        interactions = user.interactions.all()
        
        if not interactions.exists():
            return Response({"text": "Aucune interaction."}, status=status.HTTP_200_OK)
            
        lines = []
        for i in interactions:
            formatted_date = i.date_created.strftime('%d %B, %H:%M')
            lines.append(f"[{i.type_interaction}] {formatted_date} : {i.summary}")
            
        export_text = "\n".join(lines)
        return Response({"text": export_text}, status=status.HTTP_200_OK)


# ════════════════════════════════════════════════════════════════════
# BOT CONFIG DETAIL VIEW
# ════════════════════════════════════════════════════════════════════
class BotConfigDetailView(APIView):
    
    def get(self, request):
        config, created = BotConfig.objects.get_or_create(id=1)
        serializer = BotConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        config, created = BotConfig.objects.get_or_create(id=1)
        serializer = BotConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ════════════════════════════════════════════════════════════════════
# SETTINGS VIEW
# ════════════════════════════════════════════════════════════════════
class SettingsView(APIView):
    ALLOWED_LANGUAGES = ['Français', 'English', 'Malagasy']

    def get_settings_object(self):
        obj, created = SystemSettings.objects.get_or_create(
            id=1,
            defaults={
                "user_name": "Fanomezantsoa Rado",
                "user_email": "rado.andrinaivo@email.com",
                "selected_language": "Français",
                "is_two_factor_auth": True,
                "is_push_notify": True,
                "is_email_notify": False
            }
        )
        return obj

    def get(self, request, format=None):
        settings = self.get_settings_object()
        data = {
            "userName": settings.user_name,
            "userEmail": settings.user_email,
            "selectedLanguage": settings.selected_language,
            "isTwoFactorAuth": settings.is_two_factor_auth,
            "isPushNotify": settings.is_push_notify,
            "isEmailNotify": settings.is_email_notify,
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        settings = self.get_settings_object()
        
        user_name = request.data.get('userName')
        user_email = request.data.get('userEmail')
        selected_language = request.data.get('selectedLanguage')
        is_2fa = request.data.get('isTwoFactorAuth')
        is_push = request.data.get('isPushNotify')
        is_email_notif = request.data.get('isEmailNotify')

        if not user_name or str(user_name).strip() == "":
            return Response({"error": "Le nom complet ne peut pas être vide."}, status=status.HTTP_400_BAD_REQUEST)

        if not user_email:
            return Response({"error": "L'adresse email est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)
        
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, user_email):
            return Response({"error": "Format de l'adresse email invalide."}, status=status.HTTP_400_BAD_REQUEST)

        if selected_language is not None:
            if selected_language not in self.ALLOWED_LANGUAGES:
                return Response({"error": "Langue non supportée."}, status=status.HTTP_400_BAD_REQUEST)
            settings.selected_language = selected_language

        settings.user_name = str(user_name).strip()
        settings.user_email = str(user_email).strip()
        
        if is_2fa is not None:
            settings.is_two_factor_auth = bool(is_2fa)
        if is_push is not None:
            settings.is_push_notify = bool(is_push)
        if is_email_notif is not None:
            settings.is_email_notify = bool(is_email_notif)

        settings.save()

        return Response({
            "message": "Paramètres mis à jour avec succès !",
            "userName": settings.user_name
        }, status=status.HTTP_200_OK)
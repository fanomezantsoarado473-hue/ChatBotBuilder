from django.urls import path, include
from rest_framework.routers import DefaultRouter
# 🟢 FANITSYANA 1: Nesorina ny 'user_settings_view' teo amin'ny import satria 'SettingsView' no ampiasaina
from .views import chat_with_ai, DashboardAnalyticsView, AppUserViewSet 
from .views import BotConfigDetailView
from .views import SettingsView, AnalyticsView


router = DefaultRouter()
router.register(r'users', AppUserViewSet, basename='appuser')

urlpatterns = [
    # URL : /api/chat/
    path('chat/', chat_with_ai, name='chat_with_ai'),
    
    # URL : /api/settings/
    path('settings/', SettingsView.as_view(), name='system-settings'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),  # <-- Ampiasao ity
    
    # URL : /api/dashboard/analytics/
    path('dashboard/analytics/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    
    
    # URL ho an'ny ViewSet (Router)
    path('', include(router.urls)), 
    
    # URL : /api/bot-config/
    path('bot-config/', BotConfigDetailView.as_view(), name='bot-config'),
    
    # 🟢 FANITSYANA 2: Nesorina ilay 'dashboard/analytics/' faharoa teto mba tsy hisy doplus (duplicate)
]
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Home page
def home(request):
    return JsonResponse({
        "message": "Bienvenue sur ChatBotBuilder API!",
        "endpoints": {
            "admin": "/admin/",
            "api_chat": "/api/chat/",
            "api_settings": "/api/settings/",
            "api_analytics": "/api/analytics/",
            "api_dashboard": "/api/dashboard/analytics/",
            "api_users": "/api/users/",
            "api_bot_config": "/api/bot-config/"
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', home, name='home'),  # <-- Ampio ity raha tianao hisy pejy ao amin'ny /
]
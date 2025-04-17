# restaurants/context_processors.py
from django.conf import settings

def restaurant_context(request):
    """Context processor para informações globais do restaurante"""
    context = {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Sistema de Restaurante'),
        'CURRENT_YEAR': getattr(settings, 'CURRENT_YEAR', '2025'),
    }
    
    # Adicione aqui qualquer informação que deseja disponibilizar globalmente
    if request.user.is_authenticated:
        try:
            context['current_restaurant'] = request.user.restaurants.first()
        except AttributeError:
            pass
            
    return context

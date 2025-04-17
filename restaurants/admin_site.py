# restaurants/admin_site.py
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class RestaurantAdminSite(AdminSite):
    site_header = _('Administração do Sistema de Restaurantes')
    site_title = _('Sistema de Restaurantes')
    index_title = _('Bem-vindo ao Painel de Controle')
    
    def get_app_list(self, request):
        """
        Personaliza a ordem dos apps no admin
        """
        app_list = super().get_app_list(request)
        # Reorganize conforme necessário
        return app_list

restaurant_admin_site = RestaurantAdminSite(name='restaurant_admin')
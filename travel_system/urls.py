"""
Roteamento principal do projeto.

Os arquivos de mídia (notas fiscais) NÃO são expostos aqui. Servir MEDIA_ROOT
diretamente deixaria qualquer documento acessível a quem descobrisse a URL,
sem passar por autenticação. A entrega é feita pela view protegida
travels.views.nota_fiscal.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("travels.urls")),
]

# Em desenvolvimento o Django serve os estáticos pelo runserver.
# Em produção quem serve é o servidor web ou o WhiteNoise.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

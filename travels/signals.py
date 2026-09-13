"""
Signals do app travels.

Ficavam no fim do models.py, com os imports no meio do arquivo. Separados
aqui, o models.py volta a conter só a definição dos dados, e fica explícito
para quem lê o projeto que existe comportamento automático ligado ao User.

O registro acontece em TravelsConfig.ready() (veja apps.py).
"""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def criar_perfil_do_usuario(sender, instance, created, **kwargs):
    """Todo usuário novo nasce com um perfil, por padrão SOLICITANTE."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def salvar_perfil_do_usuario(sender, instance, created, **kwargs):
    """
    Mantém o perfil salvo junto com o usuário.

    O created=False evita salvar duas vezes no cadastro: o signal acima acaba
    de criar o perfil, não há o que atualizar.
    """
    if not created and hasattr(instance, "profile"):
        instance.profile.save()

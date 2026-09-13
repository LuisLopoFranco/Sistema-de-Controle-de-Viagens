"""
Controle de acesso por perfil.

A verificação `if request.user.profile.user_type != 'APROVADOR'` estava
repetida em quatro views, cada uma com sua própria mensagem de erro. Regra
duplicada é regra que uma hora sai do lugar: basta alguém criar a quinta view
e esquecer a checagem.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

MENSAGEM_SEM_PERMISSAO = "Você não tem permissão para acessar esta página."


def aprovador_required(view):
    """
    Restringe a view a usuários com perfil de aprovador.

    Já inclui o login_required, então basta um decorator por view. A ordem
    importa: sem autenticar primeiro, request.user seria anônimo e não teria
    o atributo profile.
    """

    @wraps(view)
    @login_required
    def _verificar(request, *args, **kwargs):
        if request.user.profile.user_type != "APROVADOR":
            messages.error(request, MENSAGEM_SEM_PERMISSAO)
            return redirect("home")
        return view(request, *args, **kwargs)

    return _verificar

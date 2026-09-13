from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from .models import TravelRequest, BankAccount, UserProfile
from .forms import (
    UserRegistrationForm,
    BankAccountForm,
    TravelRequestForm,
    TravelApprovalForm
)
from django.core.paginator import Paginator
from django.http import FileResponse, Http404

from .permissions import aprovador_required

# Quantas solicitações por página nas listagens.
TAMANHO_PAGINA = 20


def _querystring_filtros(request):
    """
    Devolve os parâmetros da URL sem o 'page', prontos para concatenar.

    Os links de paginação precisam disso: sem preservar os filtros, ir para a
    página 2 descartaria o status e o período que o usuário selecionou.
    """
    parametros = request.GET.copy()
    parametros.pop('page', None)
    codificado = parametros.urlencode()
    return f'&{codificado}' if codificado else ''

def register(request):
    """Registro de novo usuário"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'travels/register.html', {'form': form})


@login_required
def home(request):
    """Página inicial - redireciona conforme o perfil do usuário"""
    user_profile = request.user.profile

    if user_profile.user_type == 'APROVADOR':
        return redirect('dashboard')
    else:
        return redirect('my_requests')


@login_required
def my_requests(request):
    """Lista de solicitações do usuário logado"""
    requests = TravelRequest.objects.filter(
        solicitante=request.user
    ).select_related('aprovador', 'conta_bancaria')

    # As estatísticas usam o queryset completo; só a listagem é paginada.
    pagina = Paginator(requests, TAMANHO_PAGINA).get_page(request.GET.get('page'))

    context = {
        'requests': pagina,
        'page_obj': pagina,
        'querystring_filtros': _querystring_filtros(request),
        'total_gasto': requests.filter(status='APROVADA').aggregate(
            total=Sum('valor_total_combustivel')
        )['total'] or Decimal('0.00'),
        'pendentes': requests.filter(status='PENDENTE').count(),
        'aprovadas': requests.filter(status='APROVADA').count(),
        'rejeitadas': requests.filter(status='REJEITADA').count(),
    }

    return render(request, 'travels/my_requests.html', context)


@login_required
def create_request(request):
    """Criar nova solicitação de viagem"""
    # Verificar se o usuário tem conta bancária cadastrada
    has_bank_account = hasattr(request.user, 'bank_account')

    if not has_bank_account:
        messages.warning(
            request,
            'Você precisa cadastrar uma conta bancária antes de solicitar uma viagem.'
        )
        return redirect('bank_account')

    if request.method == 'POST':
        form = TravelRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            travel_request = form.save(commit=False)
            travel_request.solicitante = request.user
            travel_request.save()
            messages.success(request, 'Solicitação de viagem criada com sucesso!')
            return redirect('my_requests')
    else:
        form = TravelRequestForm(user=request.user)

    return render(request, 'travels/create_request.html', {'form': form})


@login_required
def request_detail(request, pk):
    """Detalhes de uma solicitação"""
    travel_request = get_object_or_404(TravelRequest, pk=pk)

    # Verificar permissão
    user_profile = request.user.profile
    if user_profile.user_type != 'APROVADOR' and travel_request.solicitante != request.user:
        messages.error(request, 'Você não tem permissão para visualizar esta solicitação.')
        return redirect('home')

    return render(request, 'travels/request_detail.html', {'travel_request': travel_request})


def _decidir_solicitacao(request, pk, novo_status, mensagem_sucesso, acao):
    """
    Aprova ou rejeita uma solicitação.

    As duas operações eram funções separadas e idênticas, diferindo apenas no
    status gravado e no texto da mensagem. Unificadas aqui, uma correção de
    regra vale para as duas — antes era preciso lembrar de editar nos dois
    lugares.
    """
    travel_request = get_object_or_404(TravelRequest, pk=pk)

    if travel_request.status != 'PENDENTE':
        messages.warning(request, 'Esta solicitação já foi processada.')
        return redirect('all_requests')

    if request.method == 'POST':
        form = TravelApprovalForm(request.POST)
        if form.is_valid():
            travel_request.status = novo_status
            travel_request.aprovador = request.user
            travel_request.data_aprovacao = timezone.now()
            travel_request.observacoes_aprovador = form.cleaned_data.get('observacoes', '')
            travel_request.save()
            messages.success(request, mensagem_sucesso)
            return redirect('all_requests')
    else:
        form = TravelApprovalForm()

    return render(request, 'travels/approve_request.html', {
        'travel_request': travel_request,
        'form': form,
        'action': acao,
    })


@aprovador_required
def approve_request(request, pk):
    """Aprovar uma solicitação de viagem."""
    return _decidir_solicitacao(
        request, pk,
        novo_status='APROVADA',
        mensagem_sucesso='Solicitação aprovada com sucesso!',
        acao='aprovar',
    )


@aprovador_required
def reject_request(request, pk):
    """Rejeitar uma solicitação de viagem."""
    return _decidir_solicitacao(
        request, pk,
        novo_status='REJEITADA',
        mensagem_sucesso='Solicitação rejeitada.',
        acao='rejeitar',
    )


@aprovador_required
def all_requests(request):
    """Lista de todas as solicitações - apenas para aprovadores"""
    # Filtros
    status_filter = request.GET.get('status', '')
    solicitante_filter = request.GET.get('solicitante', '')
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')

    # select_related evita uma consulta por linha ao exibir o nome do
    # solicitante e a conta bancária no template (problema N+1).
    requests = TravelRequest.objects.select_related(
        'solicitante', 'aprovador', 'conta_bancaria'
    )

    if status_filter:
        requests = requests.filter(status=status_filter)

    if solicitante_filter:
        requests = requests.filter(
            Q(solicitante__username__icontains=solicitante_filter) |
            Q(solicitante__first_name__icontains=solicitante_filter) |
            Q(solicitante__last_name__icontains=solicitante_filter)
        )

    if data_inicial:
        requests = requests.filter(data_viagem__gte=data_inicial)

    if data_final:
        requests = requests.filter(data_viagem__lte=data_final)

    pagina = Paginator(requests, TAMANHO_PAGINA).get_page(request.GET.get('page'))

    context = {
        'requests': pagina,
        'page_obj': pagina,
        'querystring_filtros': _querystring_filtros(request),
        'status_filter': status_filter,
        'solicitante_filter': solicitante_filter,
        'data_inicial': data_inicial,
        'data_final': data_final,
    }

    return render(request, 'travels/all_requests.html', context)


@aprovador_required
def dashboard(request):
    """Dashboard para aprovadores"""
    # Filtros
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')

    requests = TravelRequest.objects.all()

    if data_inicial:
        requests = requests.filter(data_viagem__gte=data_inicial)

    if data_final:
        requests = requests.filter(data_viagem__lte=data_final)

    # Estatísticas gerais
    total_requests = requests.count()
    total_pendentes = requests.filter(status='PENDENTE').count()
    total_aprovadas = requests.filter(status='APROVADA').count()
    total_rejeitadas = requests.filter(status='REJEITADA').count()

    # Total gasto
    total_gasto = requests.filter(status='APROVADA').aggregate(
        total=Sum('valor_total_combustivel')
    )['total'] or Decimal('0.00')

    # Ranking de solicitantes por valor
    ranking_valor = requests.filter(status='APROVADA').values(
        'solicitante__first_name',
        'solicitante__last_name',
        'solicitante__username'
    ).annotate(
        total_gasto=Sum('valor_total_combustivel')
    ).order_by('-total_gasto')[:10]

    # Ranking de solicitantes por número de viagens
    ranking_viagens = requests.filter(status='APROVADA').values(
        'solicitante__first_name',
        'solicitante__last_name',
        'solicitante__username'
    ).annotate(
        num_viagens=Count('id')
    ).order_by('-num_viagens')[:10]

    # Solicitações recentes
    recent_requests = requests.order_by('-data_criacao')[:5]

    context = {
        'total_requests': total_requests,
        'total_pendentes': total_pendentes,
        'total_aprovadas': total_aprovadas,
        'total_rejeitadas': total_rejeitadas,
        'total_gasto': total_gasto,
        'ranking_valor': ranking_valor,
        'ranking_viagens': ranking_viagens,
        'recent_requests': recent_requests,
        'data_inicial': data_inicial,
        'data_final': data_final,
    }

    return render(request, 'travels/dashboard.html', context)


@login_required
def bank_account(request):
    """Gerenciar conta bancária - apenas para solicitantes"""
    # Verificar se o usuário é solicitante
    if request.user.profile.user_type != 'SOLICITANTE':
        messages.error(request, 'Apenas solicitantes podem cadastrar contas bancárias.')
        return redirect('home')

    try:
        account = request.user.bank_account
        is_new = False
    except BankAccount.DoesNotExist:
        account = None
        is_new = True

    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=account)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.user = request.user
            bank_account.save()
            messages.success(request, 'Dados bancários salvos com sucesso!')
            return redirect('my_requests')
    else:
        form = BankAccountForm(instance=account)

    return render(request, 'travels/bank_account.html', {
        'form': form,
        'is_new': is_new
    })
@login_required
def nota_fiscal(request, pk):
    """
    Entrega o arquivo da nota fiscal apenas a quem pode vê-lo.

    Antes, os arquivos ficavam em MEDIA_ROOT servido diretamente pelo
    servidor web: qualquer pessoa com a URL baixava o documento sem estar
    autenticada. Notas fiscais contêm dados pessoais, então a entrega passa
    a depender da mesma regra de permissão da tela de detalhe.
    """
    solicitacao = get_object_or_404(TravelRequest, pk=pk)

    eh_aprovador = request.user.profile.user_type == 'APROVADOR'
    eh_dono = solicitacao.solicitante_id == request.user.id
    if not (eh_aprovador or eh_dono):
        # 404 em vez de 403: negar sem confirmar que a solicitação existe.
        raise Http404

    if not solicitacao.nota_fiscal:
        raise Http404

    return FileResponse(solicitacao.nota_fiscal.open('rb'))


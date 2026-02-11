from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.db import models
from django.views.decorators.http import require_http_methods
import io
import json
import logging
import pandas as pd
from .models import MedicaoGravimetrica, CustomUser
from .forms import MedicaoGravimetricaForm, SignUpForm, LoginForm, UserProfileForm
from .models import MedicaoGravimetrica
from .forms import UploadExcelForm

logger = logging.getLogger(__name__)


# ============================================================================
# AUTHENTICATION VIEWS - Sign Up, Login, Logout, Profile
# ============================================================================

@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Página de registro de novo usuário"""
    if request.user.is_authenticated:
        return redirect('medicoes:home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Bem-vindo {user.first_name}! Sua conta foi criada com sucesso. '
                f'Agora você pode fazer login.'
            )
            return redirect('medicoes:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SignUpForm()
    
    return render(request, 'medicoes/signup.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Página de login de usuário"""
    if request.user.is_authenticated:
        return redirect('medicoes:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Tenta primeiro com username
            user = authenticate(username=username_or_email, password=password)
            
            # Se não funcionar, tenta com email
            if user is None and '@' in username_or_email:
                try:
                    user_obj = CustomUser.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo de volta, {user.first_name or user.username}!')
                return redirect('medicoes:home')
            else:
                messages.error(request, 'Email/Usuário ou senha incorretos.')
    else:
        form = LoginForm()
    
    return render(request, 'medicoes/login.html', {'form': form})


@login_required
@require_http_methods(["GET"])
def logout_view(request):
    """Realiza logout do usuário"""
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('medicoes:login')


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """Página de perfil do usuário"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('medicoes:profile')
        else:
            messages.error(request, 'Erro ao atualizar o perfil. Verifique os dados.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'medicoes/profile.html', {
        'form': form,
        'user_type_display': request.user.get_user_type_display()
    })


# ============================================================================
# HELPER FUNCTIONS FOR USER TYPE CHECKING
# ============================================================================

def is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_authenticated and user.is_admin()


def is_operator(user):
    """Verifica se o usuário é operador"""
    return user.is_authenticated and user.is_operator()


def is_operator_or_admin(user):
    """Verifica se o usuário é operador ou administrador"""
    return user.is_authenticated and (user.is_operator() or user.is_admin())


# ============================================================================
# MEDICOES VIEWS - Com restrições de permissão baseadas em user_type
# ============================================================================

class MedicaoListView(ListView):
    """Lista todas as medições gravimétricas com filtros avançados"""
    model = MedicaoGravimetrica
    template_name = 'medicoes/lista.html'
    context_object_name = 'medicoes'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('medicoes:login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = MedicaoGravimetrica.objects.all()
        
        # Filtro de busca por texto
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                models.Q(nome_estacao__icontains=search) |
                models.Q(codigo_estacao__icontains=search) |
                models.Q(operador__icontains=search)
            )
        
        # Filtro por data inicial
        data_inicio = self.request.GET.get('data_inicio', '')
        if data_inicio:
            from datetime import datetime
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(data_medicao__gte=data_inicio_dt)
            except ValueError:
                pass
        
        # Filtro por data final
        data_fim = self.request.GET.get('data_fim', '')
        if data_fim:
            from datetime import datetime
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
                queryset = queryset.filter(data_medicao__lte=data_fim_dt)
            except ValueError:
                pass
        
        # Filtro por operador
        operador = self.request.GET.get('operador', '')
        if operador:
            queryset = queryset.filter(operador__icontains=operador)
        
        # Filtro por gravidade mínima
        gravidade_min = self.request.GET.get('gravidade_min', '')
        if gravidade_min:
            try:
                queryset = queryset.filter(valor_gravidade__gte=float(gravidade_min))
            except ValueError:
                pass
        
        # Filtro por gravidade máxima
        gravidade_max = self.request.GET.get('gravidade_max', '')
        if gravidade_max:
            try:
                queryset = queryset.filter(valor_gravidade__lte=float(gravidade_max))
            except ValueError:
                pass
        
        # Mostrar todas as medições (ativas e inativas para admin)
        if not self.request.user.is_admin():
            queryset = queryset.filter(ativo=True)
        
        return queryset.order_by('-data_medicao')


class MedicaoCreateView(CreateView):
    """Cria uma nova medição gravimétrica - Apenas para Operadores e Administradores"""
    model = MedicaoGravimetrica
    form_class = MedicaoGravimetricaForm
    template_name = 'medicoes/form.html'
    success_url = reverse_lazy('medicoes:medicao_lista')
    
    def dispatch(self, request, *args, **kwargs):
        if not is_operator_or_admin(request.user):
            messages.error(request, 'Você não tem permissão para adicionar medições.')
            return redirect('medicoes:medicao_lista')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, 'Medição gravimétrica cadastrada com sucesso!')
        return super().form_valid(form)


class MedicaoUpdateView(UpdateView):
    """Atualiza uma medição gravimétrica existente - Apenas para Operadores e Administradores"""
    model = MedicaoGravimetrica
    form_class = MedicaoGravimetricaForm
    template_name = 'medicoes/form.html'
    success_url = reverse_lazy('medicoes:medicao_lista')
    
    def dispatch(self, request, *args, **kwargs):
        if not is_operator_or_admin(request.user):
            messages.error(request, 'Você não tem permissão para editar medições.')
            return redirect('medicoes:medicao_lista')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Medição gravimétrica atualizada com sucesso!')
        return super().form_valid(form)


class MedicaoDeleteView(DeleteView):
    """Remove uma medição gravimétrica - Apenas para Administradores"""
    model = MedicaoGravimetrica
    template_name = 'medicoes/confirmar_exclusao.html'
    success_url = reverse_lazy('medicoes:medicao_lista')
    
    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, 'Apenas administradores podem deletar medições.')
            return redirect('medicoes:medicao_lista')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Medição gravimétrica removida com sucesso!')
        return super().delete(request, *args, **kwargs)


def gerar_pdf_medicao(request, pk):
    """Gera PDF de uma medição específica"""
    if not request.user.is_authenticated:
        return redirect('medicoes:login')
    
    medicao = get_object_or_404(MedicaoGravimetrica, pk=pk)
    
    # Preparar caminhos de arquivo absoluto para WeasyPrint carregar imagens diretamente
    import os
    foto_path = None
    croqui_path = None

    try:
        if medicao.foto_estacao and hasattr(medicao.foto_estacao, 'path'):
            foto_fs = medicao.foto_estacao.path
            if os.path.exists(foto_fs):
                foto_path = f"file://{foto_fs}"
            else:
                try:
                    foto_path = request.build_absolute_uri(medicao.foto_estacao.url)
                except Exception as e:
                    logger.error(f"Erro ao construir foto URL absoluta: {e}")
    except Exception as e:
        logger.error(f"Erro ao acessar foto_estacao.path: {e}")

    try:
        if medicao.croqui and hasattr(medicao.croqui, 'path'):
            croqui_fs = medicao.croqui.path
            if os.path.exists(croqui_fs):
                croqui_path = f"file://{croqui_fs}"
            else:
                try:
                    croqui_path = request.build_absolute_uri(medicao.croqui.url)
                except Exception as e:
                    logger.error(f"Erro ao construir croqui URL absoluta: {e}")
    except Exception as e:
        logger.error(f"Erro ao acessar croqui.path: {e}")

    html_string = render_to_string('medicoes/pdf_template.html', {
        'medicao': medicao,
        'foto_path': foto_path,
        'croqui_path': croqui_path,
    })
    # Gerar data URIs para imagens
    try:
        import base64
        import mimetypes
        from django.conf import settings as django_settings

        # Logo
        logo_data = None
        try:
            logo_fs = os.path.join(django_settings.BASE_DIR, 'static', 'medicoes', 'logo.svg')
            if os.path.exists(logo_fs):
                with open(logo_fs, 'rb') as f:
                    logo_bytes = f.read()
                mime, _ = mimetypes.guess_type(logo_fs)
                mime = mime or 'image/svg+xml'
                logo_b64 = base64.b64encode(logo_bytes).decode('ascii')
                logo_data = f'data:{mime};base64,{logo_b64}'
        except Exception as e:
            logger.error(f"Erro ao gerar logo_data: {e}")

        # Foto da estação
        foto_data = None
        try:
            if foto_path and foto_path.startswith('file://'):
                foto_fs = foto_path[len('file://'):]
                if os.path.exists(foto_fs):
                    with open(foto_fs, 'rb') as f:
                        b = f.read()
                    mime, _ = mimetypes.guess_type(foto_fs)
                    mime = mime or 'image/jpeg'
                    foto_data = f'data:{mime};base64,' + base64.b64encode(b).decode('ascii')
        except Exception as e:
            logger.error(f"Erro ao gerar foto_data: {e}")

        # Croqui
        croqui_data = None
        try:
            if croqui_path and croqui_path.startswith('file://'):
                croqui_fs = croqui_path[len('file://'):]
                if os.path.exists(croqui_fs):
                    with open(croqui_fs, 'rb') as f:
                        b = f.read()
                    mime, _ = mimetypes.guess_type(croqui_fs)
                    mime = mime or 'image/jpeg'
                    croqui_data = f'data:{mime};base64,' + base64.b64encode(b).decode('ascii')
        except Exception as e:
            logger.error(f"Erro ao gerar croqui_data: {e}")

        # Se não gerou croqui_data a partir de file://, tentar buscar via URL absoluto
        try:
            if not croqui_data and medicao.croqui:
                try:
                    abs_url = request.build_absolute_uri(medicao.croqui.url)
                    import urllib.request
                    with urllib.request.urlopen(abs_url) as resp:
                        b = resp.read()
                    mime, _ = mimetypes.guess_type(medicao.croqui.url)
                    mime = mime or resp.headers.get_content_type() or 'image/jpeg'
                    croqui_data = f'data:{mime};base64,' + base64.b64encode(b).decode('ascii')
                    print(f"[PDF DEBUG] croqui_data fetched from URL, length={len(b)} bytes")
                except Exception as e:
                    print(f"[PDF DEBUG] falha ao buscar croqui via URL: {e}")
        except Exception as e:
            print(f"[PDF DEBUG] erro no fallback URL para croqui: {e}")

    except Exception as e:
        print(f"[PDF DEBUG] erro no processamento de data URIs: {e}")

    # Passar data URIs ao template
    context = {
        'medicao': medicao,
        'foto_path': foto_path,
        'croqui_path': croqui_path,
        'foto_data': foto_data if 'foto_data' in locals() else None,
        'croqui_data': croqui_data if 'croqui_data' in locals() else None,
        'logo_data': logo_data if 'logo_data' in locals() else None,
    }

    # Re-render HTML with data URIs
    html_string = render_to_string('medicoes/pdf_template.html', context)
    # Salvar HTML gerado para depuração (opcional)
    try:
        from django.conf import settings
        debug_dir = os.path.join(settings.BASE_DIR, 'tmp_pdf_debug')
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, f'medicao_{medicao.pk}.html')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_string)
        print(f"[PDF DEBUG] HTML salvo para depuração em: {debug_file}")
    except Exception as e:
        print(f"[PDF DEBUG] não foi possível salvar HTML de depuração: {e}")
    
    # Tentar usar WeasyPrint primeiro
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        from django.conf import settings
        import os

        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        font_config = FontConfiguration()

        # Forçar uso do CSS de PDF a partir dos arquivos estáticos locais
        css_path = os.path.join(settings.BASE_DIR, 'static', 'medicoes', 'pdf.css')
        stylesheets = []
        if os.path.exists(css_path):
            stylesheets.append(CSS(filename=css_path))
        print(f"[PDF DEBUG] css_path={css_path} exists={os.path.exists(css_path)} stylesheets={stylesheets}")
        
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file, stylesheets=stylesheets, font_config=font_config)
        pdf_file.seek(0)
        
    except (ImportError, OSError):
        # Fallback para xhtml2pdf se WeasyPrint não estiver disponível
        try:
            from xhtml2pdf import pisa
            import re

            # Se houver um arquivo CSS local, injetá-lo inline para o xhtml2pdf
            try:
                css_path = os.path.join(settings.BASE_DIR, 'static', 'medicoes', 'pdf.css')
                if os.path.exists(css_path):
                    with open(css_path, 'r', encoding='utf-8') as f:
                        css_text = f.read()
                    # Substitui qualquer link para pdf.css por um bloco <style>
                    html_for_pisa = re.sub(r'<link[^>]+medicoes/pdf\.css[^>]*>', f'<style>{css_text}</style>', html_string, flags=re.I)
                else:
                    html_for_pisa = html_string
            except Exception as e:
                print(f"[PDF DEBUG] erro ao injetar CSS para xhtml2pdf: {e}")
                html_for_pisa = html_string

            pdf_file = io.BytesIO()
            result = pisa.CreatePDF(html_for_pisa, dest=pdf_file, encoding='utf-8')
            pdf_file.seek(0)

            if result.err:
                return HttpResponseServerError(
                    f"Erro ao gerar PDF com xhtml2pdf. "
                    f"Por favor, instale o WeasyPrint ou xhtml2pdf corretamente. "
                    f"Veja o arquivo INSTALACAO_WEASYPRINT_WINDOWS.md para instruções."
                )
        except ImportError:
            return HttpResponseServerError(
                "<h1>Erro: Bibliotecas de PDF não encontradas</h1>"
                "<p><strong>Opção 1 - Instalar WeasyPrint:</strong></p>"
                "<p>Siga as instruções no arquivo <code>INSTALACAO_WEASYPRINT_WINDOWS.md</code></p>"
                "<p>Ou baixe o GTK+ Runtime de: "
                "<a href='https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases'>"
                "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases</a></p>"
                "<p><strong>Opção 2 - Usar xhtml2pdf (mais fácil no Windows):</strong></p>"
                "<p>Execute: <code>pip install xhtml2pdf</code></p>"
                "<p>Depois reinicie o servidor Django.</p>"
            )
    
    filename = f"medicao_{medicao.codigo_estacao}_{medicao.data_medicao}.pdf"
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def gerar_pdf_consolidado(request):
    """Gera PDF consolidado com todas as medições ativas"""
    if not request.user.is_authenticated:
        return redirect('medicoes:login')
    
    medicoes = MedicaoGravimetrica.objects.filter(ativo=True).order_by('codigo_estacao')
    
    html_string = render_to_string('medicoes/pdf_consolidado.html', {
        'medicoes': medicoes
    })
    
    # Tentar usar WeasyPrint primeiro
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        from django.conf import settings
        import os

        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        font_config = FontConfiguration()

        css_path = os.path.join(settings.BASE_DIR, 'static', 'medicoes', 'pdf.css')
        stylesheets = []
        if os.path.exists(css_path):
            stylesheets.append(CSS(filename=css_path))

        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file, stylesheets=stylesheets, font_config=font_config)
        pdf_file.seek(0)
        
    except (ImportError, OSError):
        # Fallback para xhtml2pdf se WeasyPrint não estiver disponível
        try:
            from xhtml2pdf import pisa
            
            pdf_file = io.BytesIO()
            result = pisa.CreatePDF(html_string, dest=pdf_file, encoding='utf-8')
            pdf_file.seek(0)
            
            if result.err:
                return HttpResponseServerError(
                    f"Erro ao gerar PDF com xhtml2pdf. "
                    f"Por favor, instale o WeasyPrint ou xhtml2pdf corretamente. "
                    f"Veja o arquivo INSTALACAO_WEASYPRINT_WINDOWS.md para instruções."
                )
        except ImportError:
            return HttpResponseServerError(
                "<h1>Erro: Bibliotecas de PDF não encontradas</h1>"
                "<p><strong>Opção 1 - Instalar WeasyPrint:</strong></p>"
                "<p>Siga as instruções no arquivo <code>INSTALACAO_WEASYPRINT_WINDOWS.md</code></p>"
                "<p>Ou baixe o GTK+ Runtime de: "
                "<a href='https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases'>"
                "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases</a></p>"
                "<p><strong>Opção 2 - Usar xhtml2pdf (mais fácil no Windows):</strong></p>"
                "<p>Execute: <code>pip install xhtml2pdf</code></p>"
                "<p>Depois reinicie o servidor Django.</p>"
            )
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio_consolidado_gravimetrico.pdf"'
    return response


def home(request):
    """Página inicial com mapa e lista de medições"""
    if not request.user.is_authenticated:
        return redirect('medicoes:login')
    
    from datetime import datetime
    medicoes = MedicaoGravimetrica.objects.filter(ativo=True).order_by('-data_medicao')[:10]
    
    context = {
        'medicoes': medicoes,
        'user_type': request.user.get_user_type_display(),
        'is_operator': request.user.is_operator(),
        'is_admin': request.user.is_admin(),
        'is_viewer': request.user.is_viewer(),
        'year': datetime.now().year,
    }
    
    return render(request, 'medicoes/home.html', context)


@login_required
@require_http_methods(["GET"])
def medicoes_api(request):
    """API que retorna todas as medições ativas em formato JSON para o mapa"""
    try:
        medicoes = MedicaoGravimetrica.objects.filter(ativo=True).order_by('nome_estacao')
        
        dados = []
        for medicao in medicoes:
            try:
                dados.append({
                    'id': medicao.id,
                    'nome_estacao': medicao.nome_estacao,
                    'codigo_estacao': medicao.codigo_estacao,
                    'latitude': float(medicao.latitude),
                    'longitude': float(medicao.longitude),
                    'altitude': float(medicao.altitude) if medicao.altitude else None,
                    'data_medicao': medicao.data_medicao.strftime('%d/%m/%Y'),
                    'gravidade_medida': float(medicao.valor_gravidade),
                    'operador': medicao.operador or 'N/A',
                    'url_pdf': f'/medicoes/{medicao.pk}/pdf/',
                })
            except Exception as e:
                # Log de erro para cada medição problemática
                print(f"Erro ao processar medição {medicao.id}: {str(e)}")
                continue
        
        return JsonResponse({
            'success': True,
            'count': len(dados),
            'medicoes': dados
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'medicoes': []
        }, status=500)


@login_required
@require_http_methods(["GET"])
def medicao_detail(request, codigo_estacao):
    """Exibe detalhes de uma medição específica"""
    medicao = get_object_or_404(MedicaoGravimetrica, codigo_estacao=codigo_estacao)
    
    from datetime import datetime
    
    # Preparar dados para o template
    context = {
        'medicao': medicao,
        'year': datetime.now().year,
        'can_edit': request.user.is_authenticated and (
            request.user.is_operator() or request.user.is_admin()
        ),
        'can_delete': request.user.is_authenticated and request.user.is_admin(),
        'can_add_pdf': request.user.is_authenticated,
    }
    
    return render(request, 'medicoes/detail.html', context)


# ============================================================================
# PRIVACY VIEW
# ============================================================================

def privacy_view(request):
    """Página de Política de Privacidade"""
    from datetime import datetime
    context = {
        'year': datetime.now().year
    }
    return render(request, 'privacy.html', context)


# ============================================================================
# Importar Dados de Excel
# ============================================================================
from decimal import Decimal, InvalidOperation
from django.db import transaction
import pandas as pd

def clean_decimal(value, default=None):
    """Converte valores do Excel para Decimal aceito pelo Django."""
    if pd.isna(value) or value == "":
        return default
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except:
        return default


def normalizar_gravidade(valor):
    """
    Normaliza gravidade para padrão mGal (~978000).
    Arquivos antigos podem vir multiplicados por 10 ou 100.
    """
    if valor is None:
        return None

    valor = Decimal(valor)

    # Se valor estiver absurdamente alto, ajustar escala
    if valor > 2000000:
        valor = valor / Decimal("10")

    if valor > 2000000:
        valor = valor / Decimal("10")

    return valor


@login_required
def importar_medicoes_excel(request):

    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)

        if form.is_valid():
            arquivo = request.FILES["arquivo"]

            try:
                df = pd.read_excel(arquivo)

                # Normalizar colunas
                df.columns = [c.strip().lower() for c in df.columns]

                sucesso = 0
                erros = []

                with transaction.atomic():

                    for index, linha in df.iterrows():
                        try:
                            codigo = str(linha.get("codigo_estacao")).strip()
                            nome = str(linha.get("nome_estacao")).strip()

                            lat = clean_decimal(linha.get("latitude"))
                            lon = clean_decimal(linha.get("longitude"))

                            grav_raw = clean_decimal(linha.get("valor_gravidade"))
                            grav = normalizar_gravidade(grav_raw)

                            data_medicao = linha.get("data_medicao")

                            altitude = clean_decimal(
                                linha.get("altitude") or linha.get("altura") or linha.get("elevacao")
                            )

                            incerteza = clean_decimal(
                                linha.get("incerteza") or linha.get("erro") or linha.get("sigma")
                            )

                            # Criar objeto
                            estacao = MedicaoGravimetrica(
                                codigo_estacao=codigo,
                                nome_estacao=nome,
                                latitude=lat,
                                longitude=lon,
                                valor_gravidade=grav,
                                altitude=altitude,
                                incerteza=incerteza,
                                data_medicao=data_medicao,
                                usuario=request.user
                            )

                            estacao.full_clean()
                            estacao.save()

                            sucesso += 1

                        except Exception as e:
                            erros.append(
                                f"Linha {index+2} | Estação {codigo} → {str(e)}"
                            )

                if erros:
                    messages.warning(
                        request,
                        f"Importadas {sucesso} estações com sucesso. {len(erros)} falharam."
                    )
                    for erro in erros[:10]:
                        messages.error(request, erro)

                else:
                    messages.success(
                        request,
                        f"Todas as {sucesso} estações foram importadas com sucesso!"
                    )

                return redirect("medicoes:medicao_lista")

            except Exception as e:
                messages.error(request, f"Erro crítico ao importar: {e}")

    else:
        form = UploadExcelForm()

    return render(request, "medicoes/importar_excel.html", {"form": form})


# ============================================================================
# Deletar medições em massa
# ============================================================================

@login_required
@require_http_methods(["POST"])
def bulk_delete_medicoes(request):
    """Remove várias medições selecionadas - Apenas Admin"""

    if not request.user.is_admin():
        return JsonResponse({"success": False, "error": "Sem permissão"}, status=403)

    try:
        ids = request.POST.getlist("ids[]")

        if not ids:
            return JsonResponse({"success": False, "error": "Nenhuma estação selecionada"})

        # Apagar todas de uma vez
        deletadas, _ = MedicaoGravimetrica.objects.filter(id__in=ids).delete()

        return JsonResponse({
            "success": True,
            "message": f"{deletadas} estações removidas com sucesso!"
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


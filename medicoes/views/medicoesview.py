import io
import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from django.template.loader import render_to_string
from django.db import models

# Importações Absolutas (Garante que vai achar o models e forms)
from medicoes.models import MedicaoGravimetrica
from medicoes.forms import MedicaoGravimetricaForm
from .mapacontornoview import gerar_mapa_contorno_medicao

logger = logging.getLogger(__name__)

# ============================================================================
# HELPERS DE PERMISSÃO (Recriados com base no seu uso original)
# ============================================================================
def is_operator_or_admin(user):
    return user.is_authenticated and (user.is_operator() or user.is_admin())

def is_admin(user):
    return user.is_authenticated and user.is_admin()

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
            messages.error(request, 'Você não tem permissão para adicionar relatórios.')
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
    mapa_contorno = gerar_mapa_contorno_medicao(medicao)
    
    # Preparar caminhos de arquivo absoluto para WeasyPrint carregar imagens diretamente
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
        'mapa_contorno': mapa_contorno,
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
            from django.conf import settings

            # Se houver um arquivo CSS local, injetá-lo inline para o xhtml2pdf
            try:
                css_path = os.path.join(settings.BASE_DIR, 'static', 'medicoes', 'pdf.css')
                if os.path.exists(css_path):
                    with open(css_path, 'r', encoding='utf-8') as f:
                        css_text = f.read()
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
                    f"Por favor, instale o WeasyPrint ou xhtml2pdf corretamente."
                )
        except ImportError:
            return HttpResponseServerError(
                "<h1>Erro: Bibliotecas de PDF não encontradas</h1>"
                "<p>Execute: <code>pip install xhtml2pdf</code> ou verifique sua instalação do WeasyPrint.</p>"
            )
    
    filename = f"medicao_{medicao.codigo_estacao}_{medicao.data_medicao}.pdf"
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
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
        try:
            from xhtml2pdf import pisa
            
            pdf_file = io.BytesIO()
            result = pisa.CreatePDF(html_string, dest=pdf_file, encoding='utf-8')
            pdf_file.seek(0)
            
            if result.err:
                return HttpResponseServerError("Erro ao gerar PDF com xhtml2pdf.")
        except ImportError:
            return HttpResponseServerError("<h1>Erro: Bibliotecas de PDF não encontradas</h1>")
    
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
                    'marker_icon': medicao.marker_icon if hasattr(medicao, 'marker_icon') else 'default',
                    'marker_custom_url': medicao.marker_custom_url if hasattr(medicao, 'marker_custom_url') else None,
                    'url_pdf': f'/medicoes/{medicao.pk}/pdf/',
                })
            except Exception as e:
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
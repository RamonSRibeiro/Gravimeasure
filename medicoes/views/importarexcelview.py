import pandas as pd
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from ..forms import UploadExcelForm
from ..models import MedicaoGravimetrica

# ============================================================================
# Helpers
# ============================================================================

def clean_decimal(value, default=None):
    """Converte valores do Excel para Decimal aceito pelo Django."""
    if pd.isna(value) or value == "":
        return default
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return default

def normalizar_gravidade(valor):
    """
    Normaliza gravidade para padrão mGal (~978000).
    Arquivos antigos podem vir multiplicados por 10 ou 100.
    """
    if valor is None:
        return None

    valor = Decimal(valor)

    # Se o valor for pequeno (menor que ~2000), presumimos que está em Gal e multiplicamos por 1000
    if valor > Decimal('0') and valor < Decimal('2000'):
        valor = valor * Decimal('1000')

    # Se o valor estiver absurdamente alto (ex: >2.000.000), reduzir escala dividindo por 10
    attempts = 0
    while valor > Decimal('2000000') and attempts < 3:
        valor = valor / Decimal('10')
        attempts += 1

    return valor

# ============================================================================
# Importar Dados de Excel
# ============================================================================

@login_required
def importar_medicoes_excel(request):
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)

        if form.is_valid():
            arquivo = request.FILES["arquivo"]

            try:
                df = pd.read_excel(arquivo)
                df.columns = [c.strip().lower() for c in df.columns]

                sucesso = 0
                erros = []

                # Usando transaction.atomic para não salvar pela metade se der erro grave
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
                            erros.append(f"Linha {index+2} | Estação {codigo} → {str(e)}")

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
    # Presumindo que o método is_admin() existe no seu CustomUser
    if not request.user.is_admin():
        return JsonResponse({"success": False, "error": "Sem permissão"}, status=403)

    try:
        ids = request.POST.getlist("ids[]")

        if not ids:
            return JsonResponse({"success": False, "error": "Nenhuma estação selecionada"})

        deletadas, _ = MedicaoGravimetrica.objects.filter(id__in=ids).delete()

        return JsonResponse({
            "success": True,
            "message": f"{deletadas} estações removidas com sucesso!"
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
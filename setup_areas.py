#!/usr/bin/env python
"""
Script para popular a tabela AreaOfExpertise com os dados de category_config.py
Deve ser executado com: python manage.py shell < setup_areas.py
Ou: python setup_areas.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gravimeasure.settings')
django.setup()

from medicoes.models import AreaOfExpertise
from medicoes.category_config import EXPERTISE_AREAS

# Limpar áreas existentes
print(f"Removendo {AreaOfExpertise.objects.count()} áreas existentes...")
AreaOfExpertise.objects.all().delete()

# Criar novas áreas
print("\nCriando áreas de atuação:")
for key, data in EXPERTISE_AREAS.items():
    area = AreaOfExpertise.objects.create(
        key=key,
        label=data['label']
    )
    print(f"  ✓ {area.label} ({area.key})")

print(f"\nTotal de áreas cadastradas: {AreaOfExpertise.objects.count()}")

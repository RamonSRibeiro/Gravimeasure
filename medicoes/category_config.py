"""Configurações do sistema de categorização"""

ROLE_CATEGORIES = {
    'academic': {
        'label': 'Acadêmico',
        'description': 'Pesquisadores, professores e membros de instituições acadêmicas que desenvolvem trabalho científico',
        'icon': '🎓',
        'color': '#007bff',
    },
    'student': {
        'label': 'Estudante',
        'description': 'Alunos de graduação e pós-graduação em processo de formação',
        'icon': '👨‍🎓',
        'color': '#28a745',
    },
    'professional': {
        'label': 'Profissional',
        'description': 'Profissionais atuando nas áreas de geociências, metrologia, física e defesa',
        'icon': '👔',
        'color': '#17a2b8',
    }
}

EXPERTISE_AREAS = {
    'geosciences': {
        'label': 'Geociências',
        'description': 'Ciências da Terra, geologia, sismologia, vulcanologia',
        'icon': '🌍',
        'color': '#dc3545'
    },
    'metrology': {
        'label': 'Metrologia',
        'description': 'Medição, padrões, instrumentação e incertezas',
        'icon': '📏',
        'color': '#fd7e14'
    },
    'physics': {
        'label': 'Física',
        'description': 'Física fundamental, gravitação, astrofísica',
        'icon': '⚛️',
        'color': '#6f42c1'
    },
    'defense': {
        'label': 'Defesa',
        'description': 'Aplicações de defesa civil, segurança nacional',
        'icon': '🛡️',
        'color': '#e83e8c'
    },
    'science_communication': {
        'label': 'Divulgação Científica',
        'description': 'Comunicação, educação e disseminação científica',
        'icon': '📢',
        'color': '#20c997'
    }
}

# ============================================================================
# TIPOS DE USUÁRIO
# ============================================================================
USER_TYPES = {
    'admin': {
        'label': 'Administrador',
        'description': 'Acesso total ao sistema e gerenciamento de usuários',
        'level': 3
    },
    'operator': {
        'label': 'Operador',
        'description': 'Pode criar e editar medições',
        'level': 2
    },
    'viewer': {
        'label': 'Visualizador',
        'description': 'Pode apenas visualizar dados',
        'level': 1
    }
}

# ============================================================================
# MAPEAMENTO DE CORES
# ============================================================================
ROLE_COLORS = {k: v['color'] for k, v in ROLE_CATEGORIES.items()}
EXPERTISE_COLORS = {k: v['color'] for k, v in EXPERTISE_AREAS.items()}

# ============================================================================
# MAPEAMENTO DE ÍCONES
# ============================================================================
ROLE_ICONS = {k: v['icon'] for k, v in ROLE_CATEGORIES.items()}
EXPERTISE_ICONS = {k: v['icon'] for k, v in EXPERTISE_AREAS.items()}

# ============================================================================
# PERMISSÕES POR CATEGORIA
# ============================================================================
CATEGORY_PERMISSIONS = {
    'academic': [
        'medicoes.view_medicaogravimetrica',
        'medicoes.add_medicaogravimetrica',
        'medicoes.export_data',
    ],
    'student': [
        'medicoes.view_medicaogravimetrica',
        'medicoes.add_medicaogravimetrica',
    ],
    'professional': [
        'medicoes.view_medicaogravimetrica',
        'medicoes.add_medicaogravimetrica',
        'medicoes.change_medicaogravimetrica',
        'medicoes.export_data',
    ]
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_role_label(role_key):
    """Retorna o label legível de uma categoria"""
    return ROLE_CATEGORIES.get(role_key, {}).get('label', role_key)

def get_role_description(role_key):
    """Retorna a descrição de uma categoria"""
    return ROLE_CATEGORIES.get(role_key, {}).get('description', '')

def get_role_icon(role_key):
    """Retorna o ícone de uma categoria"""
    return ROLE_CATEGORIES.get(role_key, {}).get('icon', '👤')

def get_role_color(role_key):
    """Retorna a cor de uma categoria"""
    return ROLE_CATEGORIES.get(role_key, {}).get('color', '#6c757d')

def get_expertise_label(exp_key):
    """Retorna o label legível de uma área"""
    return EXPERTISE_AREAS.get(exp_key, {}).get('label', exp_key)

def get_expertise_description(exp_key):
    """Retorna a descrição de uma área"""
    return EXPERTISE_AREAS.get(exp_key, {}).get('description', '')

def get_expertise_icon(exp_key):
    """Retorna o ícone de uma área"""
    return EXPERTISE_AREAS.get(exp_key, {}).get('icon', '🔬')

def get_expertise_color(exp_key):
    """Retorna a cor de uma área"""
    return EXPERTISE_AREAS.get(exp_key, {}).get('color', '#6c757d')

def get_all_role_keys():
    """Retorna lista de todas as chaves de categorias"""
    return list(ROLE_CATEGORIES.keys())

def get_all_expertise_keys():
    """Retorna lista de todas as chaves de expertise"""
    return list(EXPERTISE_AREAS.keys())

# ============================================================================
# CONFIGURAÇÕES DE EXIBIÇÃO
# ============================================================================

ROLES_DISPLAY = {
    'academic': '🎓 Acadêmico',
    'student': '👨‍🎓 Estudante',
    'professional': '👔 Profissional'
}

EXPERTISE_DISPLAY = {
    'geosciences': '🌍 Geociências',
    'metrology': '📏 Metrologia',
    'physics': '⚛️ Física',
    'defense': '🛡️ Defesa',
    'science_communication': '📢 Divulgação Científica'
}

# ============================================================================
# CONSTANTES
# ============================================================================

# Número máximo de áreas de expertise por usuário
MAX_EXPERTISE_PER_USER = 5

# Requer expertise para completar perfil
REQUIRE_EXPERTISE = False

# Requer organização para usuários profissionais
REQUIRE_ORGANIZATION_FOR_PROFESSIONALS = True

# Áreas de expertise padrão para novos usuários
DEFAULT_EXPERTISE = []

# Categoria padrão para novos usuários
DEFAULT_ROLE = 'professional'

# ============================================================================
# TEMPLATES TAGS HELPER (para usar em templates Django)
# ============================================================================

def get_role_badge_class(role_key):
    """Retorna classe Bootstrap para badge"""
    color_map = {
        'academic': 'primary',
        'student': 'success',
        'professional': 'info'
    }
    return f"badge-{color_map.get(role_key, 'secondary')}"

def get_expertise_badge_class(exp_key):
    """Retorna classe Bootstrap para badge de expertise"""
    return 'badge-info'

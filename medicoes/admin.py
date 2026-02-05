from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import MedicaoGravimetrica, CustomUser, AreaOfExpertise


@admin.register(MedicaoGravimetrica)
class MedicaoGravimetricaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_estacao',
        'nome_estacao',
        'usuario',
        'latitude',
        'longitude',
        'valor_gravidade',
        'anomalia_bouguer',
        'data_medicao',
        'ativo'
    ]
    list_filter = ['ativo', 'data_medicao', 'operador', 'usuario']
    search_fields = ['codigo_estacao', 'nome_estacao', 'operador', 'usuario__username']
    readonly_fields = ['data_cadastro', 'data_atualizacao']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'nome_estacao', 'codigo_estacao', 'ativo')
        }),
        ('Localização', {
            'fields': ('latitude', 'longitude', 'altitude')
        }),
        ('Dados da Medição', {
            'fields': ('valor_gravidade', 'incerteza', 'anomalia_bouguer', 'densidade_referencia', 'data_medicao')
        }),
        ('Informações Adicionais', {
            'fields': ('operador', 'instrumento', 'observacoes')
        }),
        ('Metadados', {
            'fields': ('data_cadastro', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Administrador customizado para o usuário com categorização por grupos"""
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'role_category',
        'user_type',
        'organization',
        'get_expertise_areas',
        'created_at'
    ]
    list_filter = ['role_category', 'user_type', 'is_active', 'is_staff', 'areas', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'organization']
    readonly_fields = ['created_at', 'updated_at', 'get_expertise_areas']
    filter_horizontal = ['areas', 'groups', 'user_permissions']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'organization')
        }),
        ('Categorização de Usuário', {
            'fields': ('role_category', 'areas'),
            'description': 'Selecione a categoria e áreas de expertise do usuário'
        }),
        ('Tipo de Acesso', {
            'fields': ('user_type',),
            'description': 'Tipo de acesso ao sistema (Admin, Operador ou Visualizador)'
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_expertise_areas(self, obj):
        """Exibe as áreas de expertise do usuário"""
        areas = obj.areas.all()
        if areas:
            return ', '.join([area.label for area in areas])
        return '---'
    
    get_expertise_areas.short_description = 'Áreas de Expertise'


@admin.register(AreaOfExpertise)
class AreaOfExpertiseAdmin(admin.ModelAdmin):
    list_display = ['key', 'label']
    search_fields = ['key', 'label']

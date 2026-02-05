from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
import math
from datetime import datetime


class AreaOfExpertise(models.Model):
    """Lista de áreas de atuação/experiência para categorizar usuários."""
    KEY_CHOICES = (
        ('geosciences', 'Geociências'),
        ('metrology', 'Metrologia'),
        ('physics', 'Física'),
        ('defense', 'Defesa'),
        ('science_communication', 'Divulgação Científica'),
    )

    key = models.CharField(max_length=50, choices=KEY_CHOICES, unique=True)
    label = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Área de Atuação'
        verbose_name_plural = 'Áreas de Atuação'

    def __str__(self):
        return self.label


class CustomUser(AbstractUser):
    """Modelo de usuário customizado com tipos de categoria"""
    
    USER_TYPE_CHOICES = (
        ('admin', 'Administrador'),
        ('operator', 'Operador'),
        ('viewer', 'Visualizador'),
    )

    ROLE_CATEGORY_CHOICES = (
        ('academic', 'Acadêmico'),
        ('student', 'Estudante'),
        ('professional', 'Profissional'),
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='viewer',
        verbose_name='Tipo de Usuário',
        help_text='Categoria do usuário no sistema'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefone'
    )
    
    organization = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Organização/Instituição'
    )
    
    role_category = models.CharField(
        max_length=20,
        choices=ROLE_CATEGORY_CHOICES,
        default='professional',
        verbose_name='Categoria',
        help_text='Categoria do usuário: acadêmico, estudante ou profissional'
    )

    areas = models.ManyToManyField(
        AreaOfExpertise,
        blank=True,
        related_name='users'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix related_name conflicts with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='customuser_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='customuser_set'
    )
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    def is_admin(self):
        return self.user_type == 'admin'
    
    def is_operator(self):
        return self.user_type == 'operator'
    
    def is_viewer(self):
        return self.user_type == 'viewer'


# Validadores para MedicaoGravimetrica
def validar_imagem_tamanho(file):
    """Validador para tamanho máximo de arquivo (5MB)"""
    if file.size > 5 * 1024 * 1024:  # 5MB
        raise ValidationError('Arquivo deve ter no máximo 5MB.')


def validar_coordenadas_brasil(latitude, longitude):
    """Validador para coordenadas dentro do Brasil"""
    # Limites aproximados do Brasil: lat -33° a 5°, lon -73° a -35°
    if not (-34 <= latitude <= 6 and -74 <= longitude <= -34):
        raise ValidationError('Coordenadas devem estar dentro dos limites do Brasil.')


def validar_gravidade_range(valor):
    """Validador para range de gravidade esperado na Terra (~978000-980000 mGal)"""
    if not (977000 <= valor <= 982000):
        raise ValidationError('Valor de gravidade deve estar entre 977000 e 982000 mGal.')


class MedicaoGravimetrica(models.Model):
    """Modelo para armazenar medições gravimétricas"""
    
    # Usuário responsável pela medição
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Usuário",
        help_text="Usuário responsável pela medição",
        null=True,
        blank=True
    )
    
    # Informações básicas da estação
    nome_estacao = models.CharField(
        max_length=200,
        verbose_name="Nome da Estação",
        help_text="Nome identificador da estação gravimétrica"
    )
    codigo_estacao = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código da Estação",
        help_text="Código único da estação"
    )
    
    # Localização
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name="Latitude (graus)",
        help_text="Latitude em graus decimais"
    )
    longitude = models.DecimalField(
        max_digits=11, # Aumentado para suportar 7 casas + sinal + 180
        decimal_places=7,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name="Longitude (graus)",
        help_text="Longitude em graus decimais"
    )
    altitude = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Altitude (m)",
        help_text="Altitude em metros acima do nível do mar",
        null=True,
        blank=True
    )
    
    # Dados da medição (mGal na Terra é ~980.000, logo precisa de 6 dígitos antes da vírgula)
    valor_gravidade = models.DecimalField(
        max_digits=12, 
        decimal_places=5,
        verbose_name="Valor da Gravidade (mGal)",
        help_text="Valor da gravidade em miligals"
    )
    incerteza = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        verbose_name="Incerteza (mGal)",
        help_text="Incerteza da medição em miligals",
        null=True,
        blank=True
    )
    anomalia_bouguer = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        verbose_name="Anomalia de Bouguer (mGal)",
        help_text="Anomalia de Bouguer em miligals (calculada automaticamente)",
        null=True,
        blank=True
    )
    densidade_referencia = models.DecimalField(
    max_digits=6,
    decimal_places=3,
    verbose_name="Densidade de Referência (g/cm³)",
    default=Decimal("2.670")
    )

    
    # Informações adicionais
    data_medicao = models.DateField(
        verbose_name="Data da Medição",
        help_text="Data em que a medição foi realizada"
    )
    operador = models.CharField(
        max_length=100,
        verbose_name="Operador",
        null=True, blank=True
    )
    instrumento = models.CharField(
        max_length=100,
        verbose_name="Instrumento",
        null=True, blank=True
    )
    observacoes = models.TextField(
        verbose_name="Observações",
        null=True, blank=True
    )
    
    # Uploads de imagens
    foto_estacao = models.ImageField(
        upload_to='estacoes/%Y/%m/',
        verbose_name="Foto da Estação",
        help_text="Foto da estação gravimétrica (máx. 5MB)",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif']),
            validar_imagem_tamanho
        ]
    )
    
    croqui = models.ImageField(
        upload_to='croquis/%Y/%m/',
        verbose_name="Croqui/Desenho da Estação",
        help_text="Croqui ou desenho técnico da estação (máx. 5MB)",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif']),
            validar_imagem_tamanho
        ]
    )
    
    # Metadados
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Medição Gravimétrica"
        verbose_name_plural = "Medições Gravimétricas"
        ordering = ['-data_medicao', 'nome_estacao']
        indexes = [
            models.Index(fields=['codigo_estacao']),
            models.Index(fields=['data_medicao']),
        ]

    def calcular_anomalia_bouguer(self, densidade_referencia=2.67):
        if not self.altitude or not self.latitude or not self.valor_gravidade:
            return None
        
        # Converte para float para cálculos trigonométricos
        phi = math.radians(float(self.latitude))
        
        # Fórmula da Gravidade Normal (IAG 1967)
        # g_normal ≈ 978031.8 * (1 + 0.0053024 * sin²(φ) - 0.0000058 * sin²(2φ))
        sin_phi2 = math.sin(phi)**2
        sin_2phi2 = math.sin(2*phi)**2
        
        g_normal = Decimal('978031.8') * (
            Decimal('1') + 
            Decimal('0.0053024') * Decimal(str(sin_phi2)) - 
            Decimal('0.0000058') * Decimal(str(sin_2phi2))
        )
        
        h = Decimal(str(self.altitude))
        dens = Decimal(str(densidade_referencia))
        
        # Correções
        correcao_ar_livre = Decimal('0.3086') * h
        correcao_bouguer = Decimal('0.0419') * dens * h
        
        # Cálculo Final
        g_obs = Decimal(str(self.valor_gravidade))
        anomalia = g_obs - g_normal + correcao_ar_livre - correcao_bouguer
        
        return anomalia.quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)

    def calcular_anomalia_ar_livre(self):
        """Calcula a anomalia free-air (sem correção de Bouguer)."""
        if not self.altitude or not self.latitude or not self.valor_gravidade:
            return None

        phi = math.radians(float(self.latitude))
        sin_phi2 = math.sin(phi)**2
        sin_2phi2 = math.sin(2*phi)**2

        g_normal = Decimal('978031.8') * (
            Decimal('1') + 
            Decimal('0.0053024') * Decimal(str(sin_phi2)) - 
            Decimal('0.0000058') * Decimal(str(sin_2phi2))
        )

        h = Decimal(str(self.altitude))
        correcao_ar_livre = Decimal('0.3086') * h
        g_obs = Decimal(str(self.valor_gravidade))
        anomalia_free_air = g_obs - g_normal + correcao_ar_livre
        return anomalia_free_air.quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)

    def calcular_gradiente_vertical(self):
        """Retorna um valor aproximado do gradiente vertical (mGal/m).
        Utiliza valor padrão internacional aproximado de -0.3086 mGal/m para variação com altura.
        """
        # Valor padrão aproximado do gradiente vertical da gravidade (mGal/m)
        return Decimal('-0.3086')

    def save(self, *args, **kwargs):
        if self.anomalia_bouguer is None and self.altitude and self.valor_gravidade:
            self.anomalia_bouguer = self.calcular_anomalia_bouguer(self.densidade_referencia)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo_estacao} - {self.nome_estacao} ({self.data_medicao})"

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import MedicaoGravimetrica, CustomUser, validar_gravidade_range, AreaOfExpertise


class SignUpForm(UserCreationForm):
    """Formulário de registro de novo usuário"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@exemplo.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nome',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Sobrenome',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu sobrenome'
        })
    )
    
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        label='Tipo de Usuário',
        help_text='Selecione seu perfil de acesso',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    role_category = forms.ChoiceField(
        choices=CustomUser.ROLE_CATEGORY_CHOICES,
        required=True,
        label='Categoria',
        help_text='Acadêmico, Estudante ou Profissional',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    areas = forms.ModelMultipleChoiceField(
        queryset=AreaOfExpertise.objects.all(),
        required=False,
        label='Áreas de Atuação',
        widget=forms.CheckboxSelectMultiple
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Telefone',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(XX) XXXXX-XXXX'
        })
    )
    
    organization = forms.CharField(
        max_length=200,
        required=False,
        label='Organização/Instituição',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua organização'
        })
    )
    
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite uma senha forte'
        })
    )
    
    password2 = forms.CharField(
        label='Confirme a Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'user_type', 'role_category', 'areas', 'phone', 'organization', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remover campo username se existir, pois usamos email como identificador
        if 'username' in self.fields:
            del self.fields['username']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está cadastrado no sistema.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Gerar username a partir do email (parte antes do @)
        email = self.cleaned_data.get('email')
        username = email.split('@')[0]
        
        # Se o username já existe, adicionar um número
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user.username = username
        user.email = email
        
        if commit:
            user.save()
            # salvar as áreas, se houver
            areas = self.cleaned_data.get('areas')
            if areas:
                user.areas.set(areas)
        return user


class LoginForm(forms.Form):
    """Formulário de login customizado"""
    
    username = forms.CharField(
        label='Email ou Usuário',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu email ou nome de usuário'
        })
    )
    
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Formulário para editar perfil do usuário"""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'organization', 'role_category', 'areas')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(XX) XXXXX-XXXX'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sua organização'
            }),
            'role_category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'areas': forms.CheckboxSelectMultiple(),
        }


class MedicaoGravimetricaForm(forms.ModelForm):
    """Formulário para cadastro e edição de medições gravimétricas"""
    
    class Meta:
        model = MedicaoGravimetrica
        fields = [
            'nome_estacao',
            'codigo_estacao',
            'latitude',
            'longitude',
            'altitude',
            'valor_gravidade',
            'incerteza',
            'anomalia_bouguer',
            'densidade_referencia',
            'data_medicao',
            'operador',
            'instrumento',
            'observacoes',
            'foto_estacao',
            'croqui',
            'ativo'
        ]
        widgets = {
            'nome_estacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Estação Gravimétrica - Norte'
            }),
            'codigo_estacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: EST-001'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0000001',
                'placeholder': 'Ex: -15.7942'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0000001',
                'placeholder': 'Ex: -47.8822'
            }),
            'altitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Ex: 1158.5'
            }),
            'valor_gravidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00001',
                'placeholder': 'Ex: 978032.12345'
            }),
            'incerteza': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00001',
                'placeholder': 'Ex: 0.00123'
            }),
            'anomalia_bouguer': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00001',
                'placeholder': 'Será calculada automaticamente se deixado em branco'
            }),
            'densidade_referencia': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'Ex: 2.67 (padrão)'
            }),
            'data_medicao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'operador': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do operador'
            }),
            'instrumento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CG-5 Autograv'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações adicionais sobre a medição'
            }),
            'foto_estacao': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_foto_estacao'
            }),
            'croqui': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_croqui'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nome_estacao': 'Nome da Estação',
            'codigo_estacao': 'Código da Estação',
            'latitude': 'Latitude (graus)',
            'longitude': 'Longitude (graus)',
            'altitude': 'Altitude (m)',
            'valor_gravidade': 'Valor da Gravidade (mGal)',
            'incerteza': 'Incerteza (mGal)',
            'anomalia_bouguer': 'Anomalia de Bouguer (mGal)',
            'densidade_referencia': 'Densidade de Referência (g/cm³)',
            'data_medicao': 'Data da Medição',
            'operador': 'Operador',
            'instrumento': 'Instrumento',
            'observacoes': 'Observações',
            'foto_estacao': 'Foto da Estação',
            'croqui': 'Croqui/Desenho',
            'ativo': 'Ativo'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        valor_gravidade = cleaned_data.get('valor_gravidade')
        
        if valor_gravidade:
            try:
                validar_gravidade_range(float(valor_gravidade))
            except forms.ValidationError as e:
                self.add_error('valor_gravidade', e.message)
        
        return cleaned_data


class UploadExcelForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo Excel (.xlsx)")


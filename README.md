# Gravimeasure

## Descrição
Este projeto é uma aplicação web desenvolvida em Django para gestão de medições gravimétricas com geração de relatórios em PDF. O sistema permite que usuários registrem, visualizem e gere documentação de medições de gravidade em estações específicas.

## Funcionalidades
- 📊 Cadastro e gerenciamento de medições gravimétricas
- 👤 Autenticação de usuários com diferentes níveis de acesso (Admin, Operador, Visualizador)
- 📄 Geração de relatórios e PDFs consolidados
- 🗂️ Armazenamento de croquis e fotos das estações
- 🔒 Segurança com autenticação por usuário/email
- 📱 Interface responsiva com Bootstrap

## Requisitos do Sistema
- Python 3.12 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno

## Dependências
- Django 4.2.0+
- WeasyPrint (para geração de PDFs)
- Pillow (processamento de imagens)
- python-decouple (gerenciamento de variáveis de ambiente)
- xhtml2pdf (alternativa para PDFs em Windows)

## Instalação Rápida

### 1. Clone o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd BDG
```

### 2. Crie e ative um ambiente virtual
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
nano .env  # ou use seu editor preferido
```

**Variáveis de Ambiente Necessárias (.env):**
```
# Django Settings
DEBUG=False                          # Em desenvolvimento: True
SECRET_KEY=sua-chave-super-segura   # Mínimo 50 caracteres, única e secreta
ALLOWED_HOSTS=localhost,127.0.0.1   # Adicione seu domínio em produção

# Exemplo para produção:
# ALLOWED_HOSTS=meuprojeto.com,www.meuprojeto.com
# DEBUG=False
# SECRET_KEY=chave-aleatoria-muito-segura-min-50-chars
```

### 5. Execute as migrações do banco de dados
```bash
python manage.py migrate
```

### 6. Crie um superusuário (admin)
```bash
python manage.py createsuperuser
```
Siga as instruções para criar sua conta de administrador.

### 7. Inicie o servidor de desenvolvimento
```bash
python manage.py runserver
```

## Acessando a Aplicação

1. **Interface Web**: Acesse `http://127.0.0.1:8000/`
2. **Admin Django**: Acesse `http://127.0.0.1:8000/admin/` com suas credenciais de superusuário

## Estrutura do Projeto
```
BDG/
├── gravimeasure/          # Configurações principais do Django
│   ├── settings.py       # Configurações da aplicação
│   ├── urls.py          # Rotas principais
│   └── wsgi.py          # Arquivo WSGI para deploy
├── medicoes/            # App principal
│   ├── models.py        # Modelos de dados
│   ├── views.py         # Lógica das views
│   ├── forms.py         # Formulários
│   └── templates/       # Templates HTML
├── static/              # CSS, JS, imagens
├── media/               # Uploads de usuários
├── templates/           # Templates globais
├── manage.py            # Gerenciador Django
├── requirements.txt     # Dependências do projeto
└── .env                 # Variáveis de ambiente (não versionado)
```

## 🔐 Segurança e Boas Práticas

### ✅ Este projeto implementa:
- ✓ Variáveis de ambiente para configurações sensíveis
- ✓ SECRET_KEY gerada dinamicamente
- ✓ DEBUG desativado em produção
- ✓ ALLOWED_HOSTS configurável
- ✓ Proteção contra CSRF
- ✓ Autenticação e autorização de usuários
- ✓ Validação de dados em formulários
- ✓ Logging estruturado de erros

### ⚠️ IMPORTANTE - Para Produção:
1. **Nunca** comita o arquivo `.env` com credenciais reais
2. Gere uma nova `SECRET_KEY` para produção
3. Configure `DEBUG=False`
4. Configure `ALLOWED_HOSTS` com seu(s) domínio(s)
5. Use um banco de dados em produção (PostgreSQL recomendado)
6. Configure SSL/HTTPS
7. Use um servidor WSGI como Gunicorn
8. Configure um servidor web como Nginx

## Como Usar

### Criar Usuário
1. Clique em "Sign Up"
2. Preencha os dados solicitados
3. Selecione seu tipo de usuário e categoria
4. Faça login com suas credenciais

### Registrar Medição
1. Faça login na aplicação
2. Clique em "Nova Medição"
3. Preencha os dados da estação (nome, código, coordenadas, etc.)
4. Carregue fotos e croquis se necessário
5. Salve os dados

### Gerar Relatório PDF
1. Selecione uma medição registrada
2. Clique em "Gerar PDF" ou "PDF Consolidado"
3. O relatório será gerado e baixado automaticamente

## Desenvolvimento

### Executar testes (quando implementados)
```bash
python manage.py test medicoes
```

### Criar novas migrações
```bash
python manage.py makemigrations
python manage.py migrate
```

### Coletar arquivos estáticos
```bash
python manage.py collectstatic
```

## Problemas Comuns

### "ModuleNotFoundError: No module named 'weasyprint'"
```bash
# Reinstale as dependências
pip install -r requirements.txt
```

### "No such table: medicoes_..."
```bash
# Execute as migrações
python manage.py migrate
```

### Variáveis de ambiente não carregam
- Verifique se o arquivo `.env` existe na raiz do projeto
- Verifique o formato: `CHAVE=valor` (sem espaços extras)
- Reinicie o servidor após editar `.env`

## Contribuição
Sinta-se à vontade para contribuir com:
- Melhorias de funcionalidade
- Correções de bugs
- Otimizações de performance
- Melhorias na documentação

## Contato
[ramonr27@outlook.com]

---

**Última atualização**: 06 de março de 2026

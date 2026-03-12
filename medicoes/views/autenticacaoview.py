import logging
import secrets
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from ..models import CustomUser, PendingRegistration, AreaOfExpertise, LoginAttempt
from ..forms import SignUpForm, LoginForm, UserProfileForm

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Página de registro de novo usuário com pré-cadastro pendente"""
    if request.user.is_authenticated:
        return redirect('medicoes:home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            
            if CustomUser.objects.filter(email=email).exists() or PendingRegistration.objects.filter(email=email).exists():
                messages.error(request, 'Este email já está em uso ou aguardando ativação.')
                return redirect('medicoes:signup')

            token = secrets.token_urlsafe(32)
            payload = {
                'first_name': form.cleaned_data.get('first_name'),
                'last_name': form.cleaned_data.get('last_name'),
                'user_type': form.cleaned_data.get('user_type'),
                'role_category': form.cleaned_data.get('role_category'),
                'phone': form.cleaned_data.get('phone'),
                'organization': form.cleaned_data.get('organization'),
                'password': make_password(raw_password),
                'areas': [a.pk for a in form.cleaned_data.get('areas')],
            }

            pending = PendingRegistration.objects.create(email=email, token=token, data=payload)
            uid = urlsafe_base64_encode(force_bytes(pending.pk))
            activation_link = request.build_absolute_uri(
                reverse_lazy('medicoes:activate', kwargs={'uidb64': uid, 'token': token})
            )
            
            subject = 'Ative sua conta - Gravimeasure'
            message = render_to_string('medicoes/account_activation_email.html', {
                'user': {'first_name': payload.get('first_name'), 'username': email.split('@')[0]},
                'activation_link': activation_link,
            })
            
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False, html_message=message)
            except Exception as e:
                pending.delete()
                form.add_error(None, 'Falha ao enviar email de ativação. Verifique o endereço e tente novamente.')
                logger.exception(f'Erro ao enviar email para {email}: {str(e)}')
                return render(request, 'medicoes/signup.html', {'form': form})

            return redirect(f'{reverse_lazy("medicoes:email_confirmation")}?email={email}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SignUpForm()
    
    return render(request, 'medicoes/signup.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Página de login com proteção contra brute force"""
    if request.user.is_authenticated:
        return redirect('medicoes:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            attempt_record, _ = LoginAttempt.objects.get_or_create(identifier=username_or_email)
            
            if attempt_record.blocked_until and timezone.now() < attempt_record.blocked_until:
                messages.error(request, 'Conta bloqueada temporariamente. Tente novamente mais tarde.')
                return render(request, 'medicoes/login.html', {'form': form})
            
            if attempt_record.blocked_until and timezone.now() >= attempt_record.blocked_until:
                attempt_record.failed_attempts = 0
                attempt_record.blocked_until = None
                attempt_record.save()
            
            user = authenticate(username=username_or_email, password=password)
            
            if user is None and '@' in username_or_email:
                try:
                    user_obj = CustomUser.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    pass
            
            if user is not None:
                attempt_record.failed_attempts = 0
                attempt_record.blocked_until = None
                attempt_record.save()
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
                return redirect('medicoes:home')
            else:
                attempt_record.failed_attempts += 1
                if attempt_record.failed_attempts >= 5:
                    attempt_record.blocked_until = timezone.now() + timedelta(minutes=15)
                    messages.error(request, 'Muitas tentativas falhadas. Bloqueado por 15 minutos.')
                else:
                    remaining = 5 - attempt_record.failed_attempts
                    messages.error(request, f'Credenciais incorretas. ({remaining} tentativas restantes)')
                attempt_record.save()
    else:
        form = LoginForm()
    
    return render(request, 'medicoes/login.html', {'form': form})


@login_required
@require_http_methods(["GET"])
def logout_view(request):
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('medicoes:login')


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('medicoes:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'medicoes/profile.html', {
        'form': form,
        'user_type_display': request.user.get_user_type_display()
    })


@require_http_methods(["GET"])
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        pending = PendingRegistration.objects.get(pk=uid, token=token)
    except (TypeError, ValueError, OverflowError, PendingRegistration.DoesNotExist):
        messages.error(request, 'Link de ativação inválido.')
        return redirect('medicoes:signup')

    if timezone.now() - pending.created_at > timedelta(days=7):
        pending.delete()
        messages.error(request, 'O link expirou. Registre-se novamente.')
        return redirect('medicoes:signup')

    data = pending.data
    email = pending.email
    
    if CustomUser.objects.filter(email=email).exists():
        pending.delete()
        messages.error(request, 'Este email já foi registrado.')
        return redirect('medicoes:login')

    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    user = CustomUser.objects.create(
        username=username,
        email=email,
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        user_type=data.get('user_type', 'viewer'),
        role_category=data.get('role_category', 'professional'),
        phone=data.get('phone', ''),
        organization=data.get('organization', ''),
        is_active=True,
        password=data.get('password')
    )

    area_ids = data.get('areas', [])
    if area_ids:
        user.areas.set(AreaOfExpertise.objects.filter(pk__in=area_ids))

    pending.delete()
    messages.success(request, 'Conta ativada! Faça seu login.')
    return redirect('medicoes:login')


@require_http_methods(["GET", "POST"])
def email_confirmation_view(request):
    email = request.GET.get('email', '')
    if not email:
        return redirect('medicoes:signup')
    
    if request.method == 'POST' and request.POST.get('action') == 'resend':
        try:
            pending = PendingRegistration.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(pending.pk))
            activation_link = request.build_absolute_uri(
                reverse_lazy('medicoes:activate', kwargs={'uidb64': uid, 'token': pending.token})
            )
            message = render_to_string('medicoes/account_activation_email.html', {
                'user': {'first_name': pending.data.get('first_name'), 'username': email.split('@')[0]},
                'activation_link': activation_link,
            })
            send_mail('Ative sua conta - Gravimeasure', message, settings.DEFAULT_FROM_EMAIL, [email], html_message=message)
            messages.success(request, 'Email reenviado!')
        except Exception:
            messages.error(request, 'Erro ao reenviar.')
            
    return render(request, 'medicoes/email_confirmation.html', {'email': email})
#!/usr/bin/env python
"""
Script para testar configuração de email em produção
Use: python test_email.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gravimeasure.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Testar envio de email"""
    
    print("\n" + "="*60)
    print("Teste de Configuração de Email")
    print("="*60)
    
    print(f"\n📧 Backend: {settings.EMAIL_BACKEND}")
    print(f"🔒 DEBUG: {settings.DEBUG}")
    
    if settings.DEBUG:
        print("\n⚠️  DEBUG=True: Emails aparecerão no console em vez de serem enviados.")
        print("   Para testar email real, defina DEBUG=False no .env\n")
    
    if not settings.DEBUG:
        print(f"\n🌐 Gmail Host: {settings.EMAIL_HOST}")
        print(f"🔌 Porta: {settings.EMAIL_PORT}")
        print(f"🔐 TLS: {settings.EMAIL_USE_TLS}")
        print(f"👤 Usuário: {settings.EMAIL_HOST_USER}")
        print(f"📤 From: {settings.DEFAULT_FROM_EMAIL}")
    
    # Solicitar email para teste
    recipient_email = input("\n📮 Digite o email para receber o teste: ").strip()
    
    if not recipient_email:
        print("❌ Email inválido!")
        return False
    
    print(f"\n⏳ Enviando email de teste para {recipient_email}...\n")
    
    try:
        subject = '✓ Teste de Email - Gravimeasure'
        message = '''
Olá,

Este é um email de teste da configuração de email do Gravimeasure.

Se você recebeu este email, significa que suas credenciais estão corretas e funcionando!

Você já pode configurar o sistema para produção.

---
Gravimeasure - Banco de Dados Gravimétrico
        '''
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        if result == 1:
            print(f"✅ Email enviado com sucesso para {recipient_email}!")
            print("\n✓ Sua configuração de email está OK para produção.")
            return True
        else:
            print(f"⚠️  Email não foi enviado. Verifique as credenciais.")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        print("\nVerifique:")
        print("  1. A senha do Gmail está correta (App Password, não a senha normal)")
        print("  2. Autenticação em 2 fatores está ativada")
        print("  3. O email está no formato correto em .env")
        return False

if __name__ == '__main__':
    success = test_email()
    sys.exit(0 if success else 1)

from django.shortcuts import render

def privacy_view(request):
    """Página de Política de Privacidade"""
    from datetime import datetime
    context = {
        'year': datetime.now().year
    }
    return render(request, 'privacy.html', context)
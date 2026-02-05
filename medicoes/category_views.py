"""Views para gerenciamento de categorização de usuários"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import CustomUser, AreaOfExpertise
from .user_categories import UserCategoryManager


def is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff, login_url='medicoes:login')
@require_http_methods(["GET"])
def user_categories_dashboard(request):
    manager = UserCategoryManager()
    
    context = {
        'statistics': manager.get_users_statistics(),
        'summary': manager.get_category_summary(),
        'role_categories': manager.ROLE_CATEGORIES,
        'expertise_areas': manager.EXPERTISE_AREAS,
    }
    
    return render(request, 'medicoes/user_categories_dashboard.html', context)


@login_required
@user_passes_test(is_staff, login_url='medicoes:login')
@require_http_methods(["GET"])
def user_category_list(request, category_type, category_key):
    manager = UserCategoryManager()
    
    if category_type == 'role':
        users = manager.get_users_by_role(category_key)
        category_name = dict(manager.ROLE_CATEGORIES).get(category_key, category_key)
    elif category_type == 'expertise':
        users = manager.get_users_by_expertise(category_key)
        category_name = manager.EXPERTISE_AREAS.get(category_key, category_key)
    else:
        return JsonResponse({'error': 'Tipo de categoria inválido'}, status=400)
    
    context = {
        'category_type': category_type,
        'category_key': category_key,
        'category_name': category_name,
        'users': users.order_by('username'),
        'count': users.count(),
    }
    
    return render(request, 'medicoes/user_category_list.html', context)


@login_required
@user_passes_test(is_staff, login_url='medicoes:login')
@require_http_methods(["GET"])
def user_statistics_api(request):
    manager = UserCategoryManager()
    stats = manager.get_users_statistics()
    return JsonResponse(stats, safe=False)


@login_required
@user_passes_test(is_staff, login_url='medicoes:login')
@require_http_methods(["GET"])
def user_profile_categorization(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)
    
    manager = UserCategoryManager()
    role_info = manager.ROLE_CATEGORIES.get(user.role_category, {})
    
    context = {
        'user': user,
        'role_category': {
            'key': user.role_category,
            'label': role_info.get('label', ''),
            'description': role_info.get('description', '')
        },
        'expertise_areas': list(user.areas.values('key', 'label')),
        'all_expertise_areas': [
            {'key': k, 'label': v, 'assigned': k in user.areas.values_list('key', flat=True)}
            for k, v in manager.EXPERTISE_AREAS.items()
        ]
    }
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse(context, safe=False)
    
    return render(request, 'medicoes/user_profile_categorization.html', context)

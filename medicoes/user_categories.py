"""Gerenciador de categorização de usuários"""

from django.db.models import Q
from .models import CustomUser, AreaOfExpertise


class UserCategoryManager:
    ROLE_CATEGORIES = {
        'academic': {
            'label': 'Acadêmico',
            'description': 'Pesquisadores, professores e membros de instituições acadêmicas'
        },
        'student': {
            'label': 'Estudante',
            'description': 'Alunos de graduação e pós-graduação'
        },
        'professional': {
            'label': 'Profissional',
            'description': 'Profissionais atuando nas áreas de geociências, metrologia, física e defesa'
        }
    }
    
    EXPERTISE_AREAS = {
        'geosciences': 'Geociências',
        'metrology': 'Metrologia',
        'physics': 'Física',
        'defense': 'Defesa',
        'science_communication': 'Divulgação Científica',
    }
    
    @classmethod
    def get_users_by_role(cls, role):
        if role not in cls.ROLE_CATEGORIES:
            raise ValueError(f"Categoria inválida: {role}")

        
        return CustomUser.objects.filter(role_category=role)
    
    @classmethod
    def get_users_by_expertise(cls, expertise_key):
        try:
            area = AreaOfExpertise.objects.get(key=expertise_key)
            return area.users.all()
        except AreaOfExpertise.DoesNotExist:
            return CustomUser.objects.none()
    
    @classmethod
    def get_users_by_role_and_expertise(cls, role, expertise_key):
        return cls.get_users_by_role(role).filter(areas__key=expertise_key)
    
    @classmethod
    def get_users_statistics(cls):
        stats = {
            'total': CustomUser.objects.count(),
            'by_role': {},
            'by_expertise': {},
            'active': CustomUser.objects.filter(is_active=True).count(),
            'by_type': {}
        }
        
        for role_key, role_info in cls.ROLE_CATEGORIES.items():
            count = CustomUser.objects.filter(role_category=role_key).count()
            stats['by_role'][role_key] = {
                'label': role_info['label'],
                'count': count
            }
        
        for expertise in AreaOfExpertise.objects.all():
            stats['by_expertise'][expertise.key] = {
                'label': expertise.label,
                'count': expertise.users.count()
            }
        
        for user_type_key, user_type_label in CustomUser.USER_TYPE_CHOICES:
            count = CustomUser.objects.filter(user_type=user_type_key).count()
            stats['by_type'][user_type_key] = {
                'label': user_type_label,
                'count': count
            }
        
        return stats
    
    @classmethod
    def assign_expertise(cls, user, expertise_keys):
        areas = AreaOfExpertise.objects.filter(key__in=expertise_keys)
        user.areas.set(areas)
        user.save()
    
    @classmethod
    def bulk_categorize_users(cls, user_ids, role=None, expertise_keys=None):
        queryset = CustomUser.objects.filter(id__in=user_ids)
        count = 0
        
        for user in queryset:
            if role:
                user.role_category = role
            if expertise_keys:
                cls.assign_expertise(user, expertise_keys)
            else:
                user.save()
            count += 1
        
        return count
    
    @classmethod
    def get_category_summary(cls):
        summary = {
            'roles': {},
            'expertise': {}
        }
        
        for role_key, role_info in cls.ROLE_CATEGORIES.items():
            users = cls.get_users_by_role(role_key)
            summary['roles'][role_key] = {
                'label': role_info['label'],
                'description': role_info['description'],
                'count': users.count(),
                'users': list(users.values('id', 'username', 'first_name', 'last_name', 'email'))
            }
        
        for area in AreaOfExpertise.objects.all():
            summary['expertise'][area.key] = {
                'label': area.label,
                'count': area.users.count(),
                'users': list(area.users.values('id', 'username', 'first_name', 'last_name', 'email'))
            }
        
        return summary


def get_users_report():
    manager = UserCategoryManager()
    return {
        'statistics': manager.get_users_statistics(),
        'summary': manager.get_category_summary()
    }


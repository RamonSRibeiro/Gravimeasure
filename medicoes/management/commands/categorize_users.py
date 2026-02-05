"""Comando CLI para categorização de usuários"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from medicoes.models import CustomUser, AreaOfExpertise
from medicoes.user_categories import UserCategoryManager


class Command(BaseCommand):
    help = 'Categoriza usuários em grupos e áreas de expertise'
    
    def add_arguments(self, parser):
        parser.add_argument('--report', action='store_true', help='Relatório completo')
        parser.add_argument('--user-id', type=int, help='ID do usuário')
        parser.add_argument('--role', choices=['academic', 'student', 'professional'], help='Categoria')
        parser.add_argument('--expertise', nargs='+', choices=['geosciences', 'metrology', 'physics', 'defense', 'science_communication'], help='Áreas')
        parser.add_argument('--bulk-role', choices=['academic', 'student', 'professional'], help='Papel em lote')
        parser.add_argument('--statistics', action='store_true', help='Estatísticas')

    
    def handle(self, *args, **options):
        manager = UserCategoryManager()
        
        # Relatório completo
        if options['report']:
            self.print_report(manager)
        
        # Estatísticas
        elif options['statistics']:
            self.print_statistics(manager)
        
        # Categorizar usuário específico
        elif options['user_id']:
            self.categorize_user(options['user_id'], options['role'], options['expertise'], manager)
        
        # Atribuir papel em massa
        elif options['bulk_role']:
            self.bulk_assign_role(options['bulk_role'], manager)
        
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Use --report, --statistics, --user-id, ou --bulk-role\n'
                    'Execute: python manage.py help categorize_users'
                )
            )
    
    def print_report(self, manager):
        """Exibe relatório completo"""
        self.stdout.write(self.style.SUCCESS('\n=== RELATÓRIO DE CATEGORIZAÇÃO DE USUÁRIOS ===\n'))
        
        summary = manager.get_category_summary()
        
        # Por papel
        self.stdout.write(self.style.SUCCESS('\n--- CATEGORIAS DE PAPEL ---\n'))
        for role_key, role_data in summary['roles'].items():
            self.stdout.write(
                f"  {role_data['label'].upper()}\n"
                f"  Descrição: {role_data['description']}\n"
                f"  Total: {role_data['count']} usuários\n"
            )
            if role_data['users']:
                self.stdout.write("  Usuários:")
                for user in role_data['users']:
                    self.stdout.write(
                        f"    - {user['username']} ({user['first_name']} {user['last_name']}) - {user['email']}"
                    )
            self.stdout.write("")
        
        # Por expertise
        self.stdout.write(self.style.SUCCESS('\n--- ÁREAS DE EXPERTISE ---\n'))
        for area_key, area_data in summary['expertise'].items():
            self.stdout.write(
                f"  {area_data['label'].upper()}\n"
                f"  Total: {area_data['count']} usuários\n"
            )
            if area_data['users']:
                self.stdout.write("  Usuários:")
                for user in area_data['users']:
                    self.stdout.write(
                        f"    - {user['username']} ({user['first_name']} {user['last_name']})"
                    )
            self.stdout.write("")
    
    def print_statistics(self, manager):
        """Exibe estatísticas"""
        self.stdout.write(self.style.SUCCESS('\n=== ESTATÍSTICAS DE USUÁRIOS ===\n'))
        
        stats = manager.get_users_statistics()
        
        self.stdout.write(f"Total de usuários: {stats['total']}")
        self.stdout.write(f"Usuários ativos: {stats['active']}\n")
        
        self.stdout.write("Por Categoria de Papel:")
        for role_key, role_data in stats['by_role'].items():
            self.stdout.write(f"  - {role_data['label']}: {role_data['count']}")
        
        self.stdout.write("\nPor Tipo de Usuário:")
        for type_key, type_data in stats['by_type'].items():
            self.stdout.write(f"  - {type_data['label']}: {type_data['count']}")
        
        self.stdout.write("\nPor Área de Expertise:")
        for exp_key, exp_data in stats['by_expertise'].items():
            self.stdout.write(f"  - {exp_data['label']}: {exp_data['count']}")
    
    def categorize_user(self, user_id, role, expertise, manager):
        """Categoriza um usuário específico"""
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise CommandError(f'Usuário com ID {user_id} não encontrado')
        
        with transaction.atomic():
            if role:
                user.role_category = role
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Papel "{role}" atribuído ao usuário {user.username}')
                )
            
            if expertise:
                manager.assign_expertise(user, expertise)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Áreas de expertise atribuídas: {", ".join(expertise)}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\nUsuário "{user.username}" categorizado com sucesso!'))
    
    def bulk_assign_role(self, role, manager):
        """Atribui papel em massa a usuários sem categoria"""
        users_to_update = CustomUser.objects.filter(role_category='professional')  # padrão
        
        confirm = input(
            f'Deseja atribuir a categoria "{role}" a {users_to_update.count()} usuários? (s/n): '
        )
        
        if confirm.lower() == 's':
            updated = manager.bulk_categorize_users(
                list(users_to_update.values_list('id', flat=True)),
                role=role
            )
            self.stdout.write(self.style.SUCCESS(f'✓ {updated} usuários atualizados'))
        else:
            self.stdout.write('Operação cancelada')

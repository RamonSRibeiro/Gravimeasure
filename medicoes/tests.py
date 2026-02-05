"""Testes para categorização de usuários"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from medicoes.models import AreaOfExpertise
from medicoes.user_categories import UserCategoryManager

User = get_user_model()


class AreaOfExpertiseModelTest(TestCase):
    
    def setUp(self):
        self.geosciences = AreaOfExpertise.objects.create(
            key='geosciences',
            label='Geociências'
        )
        self.physics = AreaOfExpertise.objects.create(
            key='physics',
            label='Física'
        )
    
    def test_area_creation(self):
        self.assertEqual(self.geosciences.label, 'Geociências')
        self.assertEqual(self.geosciences.key, 'geosciences')
    
    def test_unique_key(self):
        with self.assertRaises(Exception):
            AreaOfExpertise.objects.create(
                key='geosciences',
                label='Outra Geociência'
            )
    
    def test_str_representation(self):
        self.assertEqual(str(self.geosciences), 'Geociências')


class CustomUserCategorization(TestCase):
    
    def setUp(self):
        self.geosciences = AreaOfExpertise.objects.create(
            key='geosciences',
            label='Geociências'
        )
        self.physics = AreaOfExpertise.objects.create(
            key='physics',
            label='Física'
        )
        
        self.academic = User.objects.create_user(
            username='prof_joao',
            email='joao@univ.edu',
            password='pass123',
            first_name='João',
            last_name='Silva',
            role_category='academic'
        )
        
        self.student = User.objects.create_user(
            username='aluno_maria',
            email='maria@univ.edu',
            password='pass123',
            first_name='Maria',
            last_name='Santos',
            role_category='student'
        )
        
        self.professional = User.objects.create_user(
            username='prof_carlos',
            email='carlos@empresa.com',
            password='pass123',
            first_name='Carlos',
            last_name='Costa',
            role_category='professional'
        )
    
    def test_user_role_assignment(self):
        """Testar atribuição de papel"""
        self.assertEqual(self.academic.role_category, 'academic')
        self.assertEqual(self.student.role_category, 'student')
        self.assertEqual(self.professional.role_category, 'professional')
    
    def test_user_expertise_assignment(self):
        """Testar atribuição de expertise"""
        self.academic.areas.add(self.geosciences, self.physics)
        self.academic.save()
        
        self.assertEqual(self.academic.areas.count(), 2)
        self.assertIn(self.geosciences, self.academic.areas.all())
        self.assertIn(self.physics, self.academic.areas.all())


class UserCategoryManagerTest(TestCase):
    """Testes para o gerenciador de categorias"""
    
    def setUp(self):
        """Criar dados de teste"""
        # Criar áreas
        self.geosciences = AreaOfExpertise.objects.create(
            key='geosciences',
            label='Geociências'
        )
        self.physics = AreaOfExpertise.objects.create(
            key='physics',
            label='Física'
        )
        
        # Criar usuários
        self.academic1 = User.objects.create_user(
            username='academic1',
            email='ac1@test.com',
            password='pass',
            role_category='academic'
        )
        self.academic2 = User.objects.create_user(
            username='academic2',
            email='ac2@test.com',
            password='pass',
            role_category='academic'
        )
        self.student1 = User.objects.create_user(
            username='student1',
            email='st1@test.com',
            password='pass',
            role_category='student'
        )
        
        # Atribuir expertise
        self.academic1.areas.add(self.geosciences)
        self.academic2.areas.add(self.physics)
        self.student1.areas.add(self.geosciences)
    
    def test_get_users_by_role(self):
        """Testar obtenção de usuários por papel"""
        academics = UserCategoryManager.get_users_by_role('academic')
        self.assertEqual(academics.count(), 2)
        
        students = UserCategoryManager.get_users_by_role('student')
        self.assertEqual(students.count(), 1)
    
    def test_get_users_by_expertise(self):
        """Testar obtenção de usuários por expertise"""
        geo_users = UserCategoryManager.get_users_by_expertise('geosciences')
        self.assertEqual(geo_users.count(), 2)
        
        physics_users = UserCategoryManager.get_users_by_expertise('physics')
        self.assertEqual(physics_users.count(), 1)
    
    def test_get_users_by_role_and_expertise(self):
        """Testar combinação de filtros"""
        academic_geo = UserCategoryManager.get_users_by_role_and_expertise(
            'academic', 'geosciences'
        )
        self.assertEqual(academic_geo.count(), 1)
        self.assertEqual(academic_geo.first(), self.academic1)
    
    def test_get_users_statistics(self):
        """Testar obtenção de estatísticas"""
        stats = UserCategoryManager.get_users_statistics()
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['by_role']['academic']['count'], 2)
        self.assertEqual(stats['by_role']['student']['count'], 1)
        self.assertEqual(stats['by_role']['professional']['count'], 0)
    
    def test_assign_expertise(self):
        """Testar atribuição de expertise"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@test.com',
            password='pass'
        )
        
        UserCategoryManager.assign_expertise(new_user, ['geosciences', 'physics'])
        
        self.assertEqual(new_user.areas.count(), 2)
        self.assertIn(self.geosciences, new_user.areas.all())
        self.assertIn(self.physics, new_user.areas.all())
    
    def test_bulk_categorize_users(self):
        """Testar categorização em lote"""
        user_ids = [self.academic1.id, self.academic2.id]
        
        updated = UserCategoryManager.bulk_categorize_users(
            user_ids,
            role='professional'
        )
        
        self.assertEqual(updated, 2)
        
        self.academic1.refresh_from_db()
        self.academic2.refresh_from_db()
        
        self.assertEqual(self.academic1.role_category, 'professional')
        self.assertEqual(self.academic2.role_category, 'professional')
    
    def test_get_category_summary(self):
        """Testar obtenção de resumo de categorias"""
        summary = UserCategoryManager.get_category_summary()
        
        self.assertIn('roles', summary)
        self.assertIn('expertise', summary)
        
        self.assertEqual(summary['roles']['academic']['count'], 2)
        self.assertEqual(summary['roles']['student']['count'], 1)
        self.assertEqual(summary['expertise']['geosciences']['count'], 2)
        self.assertEqual(summary['expertise']['physics']['count'], 1)
    
    def test_invalid_role(self):
        """Testar erro com papel inválido"""
        with self.assertRaises(ValueError):
            UserCategoryManager.get_users_by_role('invalid_role')

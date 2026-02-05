from django.urls import path
from . import views
from . import category_views

app_name = 'medicoes'

urlpatterns = [
    # Autenticação
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Políticas
    path('privacy/', views.privacy_view, name='privacy'),
    
    # Home
    path('', views.home, name='home'),
    
    # Categorização de Usuários
    path('admin/users/categories/', category_views.user_categories_dashboard, name='user_categories_dashboard'),
    path('admin/users/categories/<str:category_type>/<str:category_key>/', category_views.user_category_list, name='user_category_list'),
    path('admin/users/<int:user_id>/categorization/', category_views.user_profile_categorization, name='user_profile_categorization'),
    path('api/users/statistics/', category_views.user_statistics_api, name='user_statistics_api'),
    
    # API
    path('api/dados-mapa/', views.medicoes_api, name='medicoes_api'),
    
    # Medições
    path('medicoes/', views.MedicaoListView.as_view(), name='medicao_lista'),
    path('medicoes/adicionar/', views.MedicaoCreateView.as_view(), name='medicao_adicionar'),
    path('medicoes/<int:pk>/editar/', views.MedicaoUpdateView.as_view(), name='medicao_editar'),
    path('medicoes/<int:pk>/excluir/', views.MedicaoDeleteView.as_view(), name='medicao_excluir'),
    path('medicoes/<int:pk>/pdf/', views.gerar_pdf_medicao, name='medicao_pdf'),
    path('medicoes/pdf-consolidado/', views.gerar_pdf_consolidado, name='medicao_pdf_consolidado'),
    path('medicao/<str:codigo_estacao>/', views.medicao_detail, name='medicao_detail'),
    path("importar-excel/", views.importar_medicoes_excel, name="importar_excel"),
    path("bulk-delete/", views.bulk_delete_medicoes, name="bulk_delete"),
]  

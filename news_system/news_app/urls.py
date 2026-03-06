from django.urls import path
from . import views
from .api_views import SubscribedArticlesAPIView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('journalist/', views.journalist_dashboard, name='journalist_dashboard'),
    path('journalist/submit/', views.submit_article, name='submit_article'),
    path('editor/', views.editor_dashboard, name='editor_dashboard'),
    path('editor/approve/<int:pk>/', views.approve_article, name='approve_article'),
    path('setup-permissions/', views.setup_permissions_view, name='setup_permissions'),
    path('api/articles/', SubscribedArticlesAPIView.as_view(), name='api_articles'),
]

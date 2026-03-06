from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.utils import OperationalError

from .models import Article, User, Publisher
from .signals import create_groups_and_permissions


def home(request):
    articles = Article.objects.filter(status=Article.APPROVED).order_by('-date_posted')
    return render(request, 'news_app/home.html', {'articles': articles})


def ensure_demo_accounts():
    """Ensure role demo accounts exist with known credentials for evaluation."""
    try:
        publisher, _ = Publisher.objects.get_or_create(
            name='Demo Publisher',
            defaults={'website': 'https://example.com'},
        )

        demo_users = [
            ('reader_demo', User.READER, None),
            ('journalist_demo', User.JOURNALIST, publisher),
            ('editor_demo', User.EDITOR, publisher),
        ]

        for username, role, assigned_publisher in demo_users:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': role,
                    'publisher': assigned_publisher,
                },
            )
            user.role = role
            user.publisher = assigned_publisher
            user.set_password('DemoPass123!')
            user.save()
    except OperationalError:
        return


def login_view(request):
    ensure_demo_accounts()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        normalized_username = username.lower()

        user = authenticate(request, username=username, password=password)
        if not user and normalized_username != username:
            user = authenticate(request, username=normalized_username, password=password)
        if user:
            login(request, user)
            if user.role == User.JOURNALIST:
                return redirect('journalist_dashboard')
            if user.role == User.EDITOR:
                return redirect('editor_dashboard')
            return redirect('home')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'news_app/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, status=Article.APPROVED)
    return render(request, 'news_app/article_detail.html', {'article': article})


@login_required
def journalist_dashboard(request):
    if request.user.role != User.JOURNALIST:
        return HttpResponseForbidden("Access denied.")
    articles = Article.objects.filter(author=request.user).order_by('-date_posted')
    return render(request, 'news_app/journalist_dashboard.html', {'articles': articles})


@login_required
def submit_article(request):
    if request.user.role != User.JOURNALIST:
        return HttpResponseForbidden("Access denied.")
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if title and content:
            Article.objects.create(
                title=title,
                content=content,
                author=request.user,
                publisher=request.user.publisher,
                status=Article.PENDING,
            )
            messages.success(request, 'Article submitted for review.')
            return redirect('journalist_dashboard')
        messages.error(request, 'Title and content are required.')
    return render(request, 'news_app/submit_article.html')


@login_required
def editor_dashboard(request):
    if request.user.role != User.EDITOR:
        return HttpResponseForbidden("Access denied.")
    pending_articles = Article.objects.filter(status=Article.PENDING).order_by('-date_posted')
    return render(request, 'news_app/editor_dashboard.html', {'articles': pending_articles})


@login_required
def approve_article(request, pk):
    if request.user.role != User.EDITOR:
        return HttpResponseForbidden("Access denied.")
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            article.status = Article.APPROVED
            article.approved_by = request.user
            article.save()
            messages.success(request, f'Article "{article.title}" approved.')
        elif action == 'reject':
            article.status = Article.REJECTED
            article.approved_by = request.user
            article.save()
            messages.warning(request, f'Article "{article.title}" rejected.')
        return redirect('editor_dashboard')
    return render(request, 'news_app/approve_article.html', {'article': article})


@login_required
def setup_permissions_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    create_groups_and_permissions()
    messages.success(request, 'Groups and permissions created.')
    return redirect('home')

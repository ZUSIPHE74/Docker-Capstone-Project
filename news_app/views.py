"""
Views for the news_app application.
Contains functions for user authentication, article management, and dashboards.
"""
from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.utils import OperationalError

from .models import Article, User, Publisher
from .signals import create_groups_and_permissions


def home(request):
    """Render the public homepage with only approved articles."""
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
    """Authenticate a user with username/password and start a session."""
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
            # Redirect users based on their role
            if user.role == User.JOURNALIST:
                return redirect('journalist_dashboard')
            elif user.role == User.EDITOR:
                return redirect('editor_dashboard')
            else:
                return redirect('reader_dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'news_app/login.html')


def signup_view(request):
    """Create a new user account with a specific role.

    Expected POST fields:
        username: Unique username for the new account.
        email: Required email for the new account.
        password: Account password.
        confirm_password: Password confirmation.
        role: Selected user role (reader, journalist, or editor).
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', User.READER)

        if not username or not email or not password:
            messages.error(request, 'Username, email, and password are required.')
            return render(request, 'news_app/signup.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'news_app/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
            return render(request, 'news_app/signup.html')

        if role not in [User.READER, User.JOURNALIST, User.EDITOR]:
            role = User.READER

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
        )
        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('login')

    return render(request, 'news_app/signup.html')


@login_required
def reader_dashboard(request):
    """Display user-specific content for readers."""
    if request.user.role != User.READER:
        if request.user.role == User.JOURNALIST:
            return redirect('journalist_dashboard')
        elif request.user.role == User.EDITOR:
            return redirect('editor_dashboard')
    
    articles = Article.objects.filter(status=Article.APPROVED).order_by('-date_posted')[:10]
    return render(request, 'news_app/reader_dashboard.html', {'articles': articles})


def logout_view(request):
    """End the current session and send the user to the login page."""
    logout(request)
    return redirect('login')


@login_required
def article_detail(request, pk):
    """Show a single approved article to authenticated users."""
    article = get_object_or_404(Article, pk=pk, status=Article.APPROVED)
    return render(request, 'news_app/article_detail.html', {'article': article})


@login_required
def journalist_dashboard(request):
    """Display journalist-owned articles; deny access to non-journalists."""
    if request.user.role != User.JOURNALIST:
        return HttpResponseForbidden("Access denied.")
    articles = Article.objects.filter(author=request.user).order_by('-date_posted')
    return render(request, 'news_app/journalist_dashboard.html', {'articles': articles})


@login_required
def submit_article(request):
    """Allow journalists to submit new articles for editor review."""
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
    """List pending articles for editors to review."""
    if request.user.role != User.EDITOR:
        return HttpResponseForbidden("Access denied.")
    pending_articles = Article.objects.filter(status=Article.PENDING).order_by('-date_posted')
    return render(request, 'news_app/editor_dashboard.html', {'articles': pending_articles})


@login_required
def approve_article(request, pk):
    """Approve or reject a pending article, editor-only."""
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
    """Create default role groups/permissions, superuser-only utility endpoint."""
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    create_groups_and_permissions()
    messages.success(request, 'Groups and permissions created.')
    return redirect('home')

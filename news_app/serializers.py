"""Serializer definitions for publisher, author, and article API responses."""

from rest_framework import serializers
from .models import Article, Publisher, User


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher identity and profile fields."""

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'website', 'description']


class AuthorSerializer(serializers.ModelSerializer):
    """Serialize minimal author information for nested article output."""

    class Meta:
        model = User
        fields = ['id', 'username', 'role']


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize approved article payloads with nested author and publisher."""

    author = AuthorSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'date_posted', 'author', 'publisher', 'status']

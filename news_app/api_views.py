"""API views for delivering subscribed, approved articles."""

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Article
from .serializers import ArticleSerializer


class SubscribedArticlesAPIView(ListAPIView):
    """Return approved articles for the reader's subscriptions."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter approved articles by followed publishers or journalists."""
        user = self.request.user
        subscribed_publishers = user.subscribed_publishers.all()
        subscribed_journalists = user.subscribed_journalists.all()
        return Article.objects.filter(
            status=Article.APPROVED
        ).filter(
            Q(publisher__in=subscribed_publishers) | Q(author__in=subscribed_journalists)
        ).distinct().order_by('-date_posted')

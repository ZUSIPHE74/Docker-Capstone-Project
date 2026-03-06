from django.contrib.auth.models import AbstractUser
from django.db import models


class Publisher(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    READER = 'reader'
    EDITOR = 'editor'
    JOURNALIST = 'journalist'

    ROLE_CHOICES = [
        (READER, 'Reader'),
        (EDITOR, 'Editor'),
        (JOURNALIST, 'Journalist'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=READER)
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='staff'
    )

    subscribed_publishers = models.ManyToManyField(
        Publisher,
        blank=True,
        related_name='subscribers'
    )
    subscribed_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='followers'
    )

    def save(self, *args, **kwargs):
        if self.role == self.JOURNALIST:
            self.subscribed_publishers.clear() if self.pk else None
            self.subscribed_journalists.clear() if self.pk else None
        elif self.role in (self.READER, self.EDITOR):
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Article(models.Model):
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING, 'Pending Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_articles'
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='articles'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_articles'
    )

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_newsletters'
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='newsletters'
    )

    def __str__(self):
        return self.title

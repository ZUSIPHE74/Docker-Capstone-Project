from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail

from .models import Article, User


def create_groups_and_permissions():
    article_ct = ContentType.objects.get_for_model(Article)

    view_article = Permission.objects.get_or_create(codename='view_article', content_type=article_ct, defaults={'name': 'Can view article'})[0]
    add_article = Permission.objects.get_or_create(codename='add_article', content_type=article_ct, defaults={'name': 'Can add article'})[0]
    change_article = Permission.objects.get_or_create(codename='change_article', content_type=article_ct, defaults={'name': 'Can change article'})[0]
    delete_article = Permission.objects.get_or_create(codename='delete_article', content_type=article_ct, defaults={'name': 'Can delete article'})[0]

    reader_group, _ = Group.objects.get_or_create(name='Reader')
    reader_group.permissions.set([view_article])

    editor_group, _ = Group.objects.get_or_create(name='Editor')
    editor_group.permissions.set([view_article, change_article, delete_article])

    journalist_group, _ = Group.objects.get_or_create(name='Journalist')
    journalist_group.permissions.set([view_article, add_article, change_article, delete_article])


@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    group_map = {
        User.READER: 'Reader',
        User.EDITOR: 'Editor',
        User.JOURNALIST: 'Journalist',
    }
    group_name = group_map.get(instance.role)
    if group_name:
        try:
            group = Group.objects.get(name=group_name)
            instance.groups.clear()
            instance.groups.add(group)
        except Group.DoesNotExist:
            pass


@receiver(post_save, sender=Article)
def notify_subscribers_on_approval(sender, instance, **kwargs):
    if instance.status != Article.APPROVED:
        return

    subscriber_emails = set()

    if instance.publisher:
        for reader in instance.publisher.subscribers.all():
            if reader.email:
                subscriber_emails.add(reader.email)

    for reader in instance.author.followers.all():
        if reader.email:
            subscriber_emails.add(reader.email)

    if subscriber_emails:
        send_mail(
            subject=f"New Article: {instance.title}",
            message=f"A new article has been published.\n\nTitle: {instance.title}\n\n{instance.content[:200]}...",
            from_email='noreply@newsapp.com',
            recipient_list=list(subscriber_emails),
            fail_silently=True,
        )

from django.core.management.base import BaseCommand
from news_app.models import User, Publisher, Article

class Command(BaseCommand):
    help = 'Create demo users, publishers, and articles for testing.'

    def handle(self, *args, **kwargs):
        # Publishers
        pub1, _ = Publisher.objects.get_or_create(name='Tech Weekly', website='http://techweekly.com')
        pub2, _ = Publisher.objects.get_or_create(name='Daily News', website='http://dailynews.com')
        pub3, _ = Publisher.objects.get_or_create(name='Global Times', website='http://globaltimes.com')

        # Reader
        reader1, _ = User.objects.get_or_create(username='reader1', role=User.READER)
        reader1.set_password('readerpass')
        reader1.save()

        # Journalist
        journalist1, _ = User.objects.get_or_create(username='journalist1', role=User.JOURNALIST, publisher=pub1)
        journalist1.set_password('journalistpass')
        journalist1.save()

        # Editor (not shown in demo logins, but needed for approval)
        editor1, _ = User.objects.get_or_create(username='editor1', role=User.EDITOR, publisher=pub1)
        editor1.set_password('editorpass')
        editor1.save()

        # Subscriptions
        reader1.subscribed_publishers.add(pub1)
        reader1.subscribed_journalists.add(journalist1)

        # Articles
        Article.objects.get_or_create(
            title='Tech Trends 2026',
            content='Latest trends in tech for 2026...',
            author=journalist1,
            publisher=pub1,
            status=Article.APPROVED,
        )
        Article.objects.get_or_create(
            title='Science Innovations',
            content='New discoveries in science for 2026.',
            author=journalist1,
            publisher=pub1,
            status=Article.APPROVED,
        )
        Article.objects.get_or_create(
            title='Pending News',
            content='This article is pending approval.',
            author=journalist1,
            publisher=pub1,
            status=Article.PENDING,
        )
        self.stdout.write(self.style.SUCCESS('Demo users, publishers, and articles created.'))

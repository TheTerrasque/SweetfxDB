from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.forum.models import ForumPost
from sweetfx_database.gamedb.openai_spamjudge import judge_post
from tqdm import tqdm
class Command(BaseCommand):
    help = 'Filter forum spam entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--progress',
            action='store_true',
            default=False,
            help='Display progress information during processing'
        )

        # Add an option for the number of posts to process (default: 10)
        parser.add_argument(
            '--num-posts',
            type=int,
            default=10,
            help='Specify the number of posts to process (default is 10)'
        )

    def handle(self, *args, **options):
        query = ForumPost.objects.filter(state = 0)[:options.get('num_posts')]
        if options.get('progress'):
            query = tqdm(query)
        for post in query:
            judge_post(post)
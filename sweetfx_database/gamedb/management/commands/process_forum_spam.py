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

        parser.add_argument(
            '--quiet',
            action='store_true',
            default=False,
            help="Don't display post information"
        )

        # Add an option for the number of posts to process (default: 10)
        parser.add_argument(
            '--num-posts',
            type=int,
            default=10,
            help='Specify the number of posts to process (default is 10)'
        )

    def handle(self, *args, **options):
        progress = options.get('progress')
        print_info = not options.get('quiet')
        query = ForumPost.objects.filter(state = 0)[:options.get('num_posts')]
        if progress:
            query = tqdm(query)
        for post in query:
            print_info and tqdm.write(f"Processing message { post.id } by { post.creator }")
            r = judge_post(post) 
            if r and print_info:
                tqdm.write(" Post judged: %s" % post.id)
                if r >= 2:
                    tqdm.write(" User %s lost post privs" % post.creator)

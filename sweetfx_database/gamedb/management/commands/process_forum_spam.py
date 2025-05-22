from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.forum.models import ForumPost
from sweetfx_database.gamedb.openai_spamjudge import OpenAISpamJudge, BASE_URL, MODEL, KEY
from tqdm import tqdm

from termcolor import colored

TYPES = {
    2: colored("SPAM", "light_red"),
    1: colored("OK", "light_green"),
    3: colored("Unsure", "light_yellow"),
    4: colored("ERROR", "light_red", "on_yellow", attrs=["bold"]),
}

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
            '--baseurl',
            default=BASE_URL,
            help="OpenAI Base URL"
        )

        parser.add_argument(
            '--key',
            default=KEY,
            help="OpenAI Key"
        )

        parser.add_argument(
            '--model',
            default=MODEL,
            help="OpenAI model"
        )

        parser.add_argument(
            '--quiet',
            action='store_true',
            default=False,
            help="Don't display post information"
        )

        # Add an option for the number of posts to process (default: 10)
        parser.add_argument(
            "-n",
            '--num-posts',
            type=int,
            default=10,
            help='Specify the number of posts to process (default is 10)'
        )

    def handle(self, *args, **options):
        oai = OpenAISpamJudge(
            options.get("baseurl"),
            options.get("key"),
            options.get("model")
        )

        progress = options.get('progress')
        print_info = not options.get('quiet')
        query = ForumPost.objects.filter(state = 0)[:options.get('num_posts')]
        if progress:
            query = tqdm(query)
        for post in query:

            
            r = oai.judge_post(post) 

            url = colored("https://sfx.thelazy.net" + post.thread.get_absolute_url(), "dark_grey")
            text = f"[{ post.id }] by { post.creator }\t{TYPES[post.state]}\t{ url }"

            if r >=2:
                text += "\tUser lost posting rights"
            print_info and tqdm.write(text)

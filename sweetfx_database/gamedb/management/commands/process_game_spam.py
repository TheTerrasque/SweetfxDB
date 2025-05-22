from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.gamedb.models import Game  # Changed from ForumPost
from sweetfx_database.gamedb.openai_spamjudge import OpenAISpamJudge, BASE_URL, MODEL, KEY
from tqdm import tqdm

from termcolor import colored

# TYPES dictionary should reference game states, assuming they are the same as post states for now
# (0, "Unchecked"), (1, "Visible"), (2, "Spam"), (3, "Unsure"), (4, "Error")
TYPES = {
    0: colored("Unchecked", "cyan"), # Added for completeness, though query filters for state=0
    1: colored("OK", "light_green"),
    2: colored("SPAM", "light_red"),
    3: colored("Unsure", "light_yellow"),
    4: colored("ERROR", "light_red", "on_yellow", attrs=["bold"]),
    5: colored("Verified SPAM", "red", attrs=["bold"]), # Added for completeness
    6: colored("Mistake", "light_blue") # Added for completeness
}

class Command(BaseCommand):
    help = 'Filter game spam entries'  # Changed help text

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
            help="Don't display game information"  # Adjusted help text
        )

        parser.add_argument(
            "-n",
            '--num-posts', # Kept as num-posts for consistency, though it's num-games now
            type=int,
            default=10,
            help='Specify the number of games to process (default is 10)' # Adjusted help text
        )

    def handle(self, *args, **options):
        oai = OpenAISpamJudge(
            options.get("baseurl"),
            options.get("key"),
            options.get("model")
        )

        progress = options.get('progress')
        print_info = not options.get('quiet')
        # Query Game objects with state=0 (Unchecked)
        query = Game.objects.filter(state=0)[:options.get('num_posts')]
        
        if progress:
            query = tqdm(query)
            
        for game in query:  # Changed from post to game
            r = oai.judge_game(game)  # Changed to judge_game

            # Assuming game.get_absolute_url() provides a relative URL
            # and using the same base URL as in process_forum_spam.py
            url = colored("https://sfx.thelazy.net" + game.get_absolute_url(), "dark_grey")
            
            # Ensure game.state is valid for TYPES, default to Unchecked if not found
            state_display = TYPES.get(game.state, colored(f"Unknown State ({game.state})", "magenta"))

            text = f"[{game.id}] '{game.title}' by {game.creator.username}\t{state_display}\t{url}"

            if r >= 2:  # Corresponds to spam states leading to permission removal
                text += "\tUser lost game posting rights" # Adjusted message
            
            if print_info: # Check print_info before writing
                tqdm.write(text)

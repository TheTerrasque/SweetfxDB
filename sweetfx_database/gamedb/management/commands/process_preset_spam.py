from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.gamedb.models import Preset  # Changed from Game
from sweetfx_database.gamedb.openai_spamjudge import OpenAISpamJudge, BASE_URL, MODEL, KEY
from tqdm import tqdm

from termcolor import colored

# TYPES dictionary references spam states (0-6)
TYPES = {
    0: colored("Unchecked", "cyan"),
    1: colored("OK", "light_green"),
    2: colored("SPAM", "light_red"),
    3: colored("Unsure", "light_yellow"),
    4: colored("ERROR", "light_red", "on_yellow", attrs=["bold"]),
    5: colored("Verified SPAM", "red", attrs=["bold"]),
    6: colored("Mistake", "light_blue")
}

class Command(BaseCommand):
    help = 'Filter preset spam entries'  # Changed help text

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
            help="Don't display preset information"  # Adjusted help text
        )

        parser.add_argument(
            "-n",
            '--num-posts', # Kept as num-posts for consistency, though it's num-presets now
            type=int,
            default=10,
            help='Specify the number of presets to process (default is 10)' # Adjusted help text
        )

    def handle(self, *args, **options):
        oai = OpenAISpamJudge(
            options.get("baseurl"),
            options.get("key"),
            options.get("model")
        )

        progress = options.get('progress')
        print_info = not options.get('quiet')
        # Query Preset objects with state=0 (Unchecked)
        query = Preset.objects.filter(state=0)[:options.get('num_posts')]
        
        if progress:
            query = tqdm(query)
            
        for preset in query:  # Changed from game to preset
            r = oai.judge_preset(preset)  # Changed to judge_preset

            # Using "https://sfx.thelazy.net" as the site URL base
            url = colored("https://sfx.thelazy.net" + preset.get_absolute_url(), "dark_grey")
            
            # Ensure preset.state is valid for TYPES, default to Unchecked if not found
            state_display = TYPES.get(preset.state, colored(f"Unknown State ({preset.state})", "magenta"))

            text = f"[{preset.id}] '{preset.title}' by {preset.creator.username}\t{state_display}\t{url}"

            if r >= 2:  # Corresponds to spam states leading to permission removal
                text += "\tUser lost game posting rights" # Message remains the same
            
            if print_info: # Check print_info before writing
                tqdm.write(text)

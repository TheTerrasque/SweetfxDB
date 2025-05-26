from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.gamedb import models as gm
from sweetfx_database.gamedb.openai_spamjudge import OpenAISpamJudge, BASE_URL, MODEL, KEY
from tqdm import tqdm
from termcolor import colored

# Adapted from process_forum_spam.py to use gm state constants and game-specific state names
TYPES = {
    gm.SUSPECTED_SPAM: colored("SUSPECTED SPAM", "light_red"),
    gm.VISIBLE: colored("OK", "light_green"),
    gm.UNSURE: colored("UNSURE", "light_yellow"),
    gm.ERROR: colored("ERROR", "light_red", "on_yellow", attrs=["bold"]),
    gm.UNCHECKED: colored("UNCHECKED", "light_blue"), # Should not usually be seen in output if processed
    gm.VERIFIED_SPAM: colored("VERIFIED SPAM", "red", attrs=["bold"]),
    gm.MISTAKEN_FOR_SPAM: colored("MISTAKEN (Marked OK)", "green"),
    # PARENT_GAME_SPAM is a state for presets, not directly for games judged by this command.
    # If a game is judged as spam, its presets might be set to PARENT_GAME_SPAM by the model logic,
    # but this command judges games, so we primarily care about game states.
}

class Command(BaseCommand):
    help = 'Filter game spam entries using OpenAI'

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
            help="Don't display game information"
        )

        parser.add_argument(
            "-n",
            '--num-posts', # Renaming to --num-games for clarity, but keeping for consistency with example if preferred
            type=int,
            default=10,
            dest='num_items', # Store in a different dest to avoid confusion if --num-posts is kept
            help='Specify the number of games to process (default is 10)'
        )

    def handle(self, *args, **options):
        oai = OpenAISpamJudge(
            base_url=options.get("baseurl"), # Ensure correct kwarg name
            key=options.get("key"),
            model=options.get("model")
        )

        if not oai.active:
            if not options.get('quiet'):
                self.stdout.write(self.style.WARNING("OpenAISpamJudge is not active. Check API key, model, and other settings. Skipping API calls."))
            return

        progress = options.get('progress')
        print_info = not options.get('quiet')
        
        query = gm.Game.objects.filter(state=gm.UNCHECKED)[:options.get('num_items')]
        
        if progress:
            # Wrap query with tqdm only if print_info is also true, or use a dummy wrapper
            iterable_query = tqdm(query, desc="Processing Games") if print_info else query
        else:
            iterable_query = query

        for game in iterable_query:
            # judge_game returns 0 (not spam), 1 (spam, rights kept), 2 (spam, rights lost)
            # or -1 if OpenAISpamJudge is not active (handled by the initial check)
            result_code = oai.judge_game(game) 

            if print_info:
                # Construct URL for the game
                try:
                    game_url_path = game.get_absolute_url()
                    url_display = colored("https://sfx.thelazy.net" + game_url_path, "dark_grey")
                except Exception: # Handle cases where URL might not be resolvable
                    url_display = colored("N/A", "dark_grey")
                
                state_display = TYPES.get(game.state, colored(str(game.state), "white"))
                text = f"[{game.id}] '{game.title}' by {game.creator.username if game.creator else 'N/A'}	{state_display}	{url_display}"

                if result_code == 2: # User lost posting rights for gamedb
                    text += f"	{colored('User lost posting rights for gamedb', 'red')}"
                elif result_code == 1: # Spam, but user kept rights
                     text += f"	{colored('Marked as spam, user rights kept', 'yellow')}"
                
                if progress and print_info:
                    tqdm.write(text)
                elif print_info: # No progress bar, but print_info is true
                    self.stdout.write(text)
        
        if print_info:
            self.stdout.write(self.style.SUCCESS('Finished processing games.'))

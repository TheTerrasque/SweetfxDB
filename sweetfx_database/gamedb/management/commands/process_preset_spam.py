from django.core.management.base import BaseCommand, CommandError
from sweetfx_database.gamedb import models as gm
from sweetfx_database.gamedb.openai_spamjudge import OpenAISpamJudge, BASE_URL, MODEL, KEY
from tqdm import tqdm
from termcolor import colored

# Adapted for Preset states
TYPES = {
    gm.UNCHECKED: colored("UNCHECKED", "light_blue"),
    gm.VISIBLE: colored("OK", "light_green"),
    gm.SUSPECTED_SPAM: colored("SUSPECTED SPAM", "light_red"),
    gm.UNSURE: colored("UNSURE", "light_yellow"),
    gm.ERROR: colored("ERROR", "light_red", "on_yellow", attrs=["bold"]),
    gm.VERIFIED_SPAM: colored("VERIFIED SPAM", "red", attrs=["bold"]),
    gm.MISTAKEN_FOR_SPAM: colored("NOT SPAM (Marked OK)", "green"),
    gm.PARENT_GAME_SPAM: colored("PARENT GAME SPAM", "light_magenta") 
    # PARENT_GAME_SPAM is included for completeness in displaying state,
    # but these presets are not intended to be processed by this script's main query.
}

class Command(BaseCommand):
    help = 'Filter preset spam entries using OpenAI'

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
            help="Don't display preset information"
        )

        parser.add_argument(
            "-n",
            '--num-items', # Changed from --num-posts to --num-items for clarity
            type=int,
            default=10,
            dest='num_items',
            help='Specify the number of presets to process (default is 10)'
        )

    def handle(self, *args, **options):
        oai = OpenAISpamJudge(
            base_url=options.get("baseurl"),
            key=options.get("key"),
            model=options.get("model")
        )

        if not oai.active:
            if not options.get('quiet'):
                self.stdout.write(self.style.WARNING("OpenAISpamJudge is not active. Check API key, model, and other settings. Skipping API calls."))
            return

        progress = options.get('progress')
        print_info = not options.get('quiet')
        
        # Filter for presets that are UNCHECKED.
        # Do NOT include PARENT_GAME_SPAM in this initial query.
        query = gm.Preset.objects.filter(state=gm.UNCHECKED)[:options.get('num_items')]
        
        if progress:
            iterable_query = tqdm(query, desc="Processing Presets") if print_info else query
        else:
            iterable_query = query
            
        processed_count = 0
        for preset in iterable_query:
            processed_count +=1
            # judge_preset returns 0 (not spam), 1 (spam, rights kept), 2 (spam, rights lost)
            # or -1 if OpenAISpamJudge is not active (handled by the initial check)
            result_code = oai.judge_preset(preset) 

            if print_info:
                # Construct URL for the preset
                try:
                    preset_url_path = preset.get_absolute_url()
                    url_display = colored("https://sfx.thelazy.net" + preset_url_path, "dark_grey")
                except Exception: 
                    url_display = colored("N/A", "dark_grey")
                
                state_display = TYPES.get(preset.state, colored(str(preset.state), "white")) # Fallback for unexpected states
                text = f"[{preset.id}] '{preset.title}' by {preset.creator.username if preset.creator else 'N/A'}	{state_display}	{url_display}"

                if result_code == 2: # User lost posting rights for gamedb
                    text += f"	{colored('User lost posting rights for gamedb', 'red')}"
                elif result_code == 1: # Spam, but user kept rights
                     text += f"	{colored('Marked as spam, user rights kept', 'yellow')}"
                
                if progress and print_info: # tqdm handles its own writing
                    tqdm.write(text)
                elif print_info: # No progress bar, but print_info is true
                    self.stdout.write(text)
        
        if print_info:
            if processed_count == 0:
                self.stdout.write(self.style.SUCCESS('No presets found in UNCHECKED state to process.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Finished processing {processed_count} presets.'))

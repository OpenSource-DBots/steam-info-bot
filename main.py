from datetime import datetime
from discord.ext import commands
import json


"""
Summary:
    Get the current time and format it to H:M:S
Returns:
    The time formatted in H:M:S
"""
def get_current_time():
    current_time = datetime.now()
    return current_time.strftime('%H:%M:%S')


"""
Summary:
    Get the value of a given key in a file (most likely json)
Returns:
    The json value that matches the key
"""
def get_json_value(file_path: str, key: str):
    with open(file_path, 'r') as cfg:
        raw_json = json.loads(cfg.read())
        return raw_json[key]


class Client(commands.Bot):

    client = commands.Bot(command_prefix='s.')

    def __init__(self):
        super().__init__(command_prefix='s.')
        self.load_extensions()

    async def on_connect(self):
        print(f'[i] [{get_current_time()}] {self.user} is connecting')

    async def on_ready(self):
        print(f'[i] [{get_current_time()}] {self.user} has connected!')

    """
    Summary:
        Run the bot
    """
    def run(self):
        try:
            self.loop.run_until_complete(self.start(get_json_value('./confidential-keys.json', 'discord_bot')))
        except:
            print(f'[!] [{get_current_time()}] Failed to run the bot. Perhaps the bot token is invalid!')

    """
    Summary:
        Load the Cog extensions
    """
    def load_extensions(self):
        extensions = ['cogs.latency', 'cogs.steam_user']

        for extension in extensions:
            try:
                self.load_extension(extension)
                print(f'[i] [{get_current_time()}] Successfully loaded extension [{extension}]')
            except:
                print(f'[!] [{get_current_time()}] Failed to load extension [{extension}].')


if __name__ == '__main__':
    client = Client()
    client.run()

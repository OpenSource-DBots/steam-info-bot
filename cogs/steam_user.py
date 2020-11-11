import discord
from discord.ext import commands
import json
import requests


"""
Summary:
    Send a http request and return the result in json
Returns:
    Result as json
"""
def send_http_request(url: str):
    result = requests.get(url=url)
    return result.json()


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


class SteamUser(commands.Cog):

    # The url to the Steam Web API which has the steam profile data
    public_data_url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/' \
                      f'?key={get_json_value(file_path="./confidential-keys.json", key="steam_web_api")}&steamids='

    def __init__(self, client):
        self.client = client

    @commands.command(name='state', aliases=['profile_state', 'user_state', 'visibility', 'profile_visibility',
                                             'user_visibility'])
    async def state(self, ctx, steam_id):
        if not self.is_valid_steam_id(steam_id):
            await self.not_valid_steam_id(ctx, steam_id)
            return

        # Result of the http request in json
        result = send_http_request(f'{self.public_data_url}{steam_id}')
        # Get the 'personastate' of the user
        state = self.get_user_state(result["response"]["players"][0]["personastate"])

        # Create a Discord embed
        embed = discord.Embed(description=f'The state of SteamID `{steam_id}` is:\n'
                                          f'{state[0]} {state[1]}',
                              color=discord.Color.from_rgb(114, 137, 218))

        await ctx.send(embed=embed)

    @commands.command(name='avatar', aliases=['get_avatar', 'profile_picture'])
    async def avatar(self, ctx, steam_id, size='full'):
        if not self.is_valid_steam_id(steam_id):
            await self.not_valid_steam_id(ctx, steam_id)
            return

        # Result of the http request in json
        result = send_http_request(f'{self.public_data_url}{steam_id}')

        # The avatar sizes that the Steam Web API provides
        valid_avatar_size = [
            'small',
            'medium',
            'full'
        ]

        # Check if the size is valid
        if size in valid_avatar_size:
            embed = discord.Embed(description=f'The avatar of SteamID `{steam_id}` is:',
                                  color=discord.Color.from_rgb(114, 137, 218))
            embed.set_footer(text=f'Avatar size: {size.capitalize()} | {self.get_avatar_size(size)}')

            # In the Steam Web API the small avatar has no prefix on the end, so change the 'small' to an empty string
            if size == 'small':
                size = ''

            embed.set_image(url=result['response']['players'][0][f'avatar{size}'])
        else:
            # Create a Discord embed
            embed = discord.Embed(description=f'{ctx.author.mention}, please select a valid size '
                                              f'<`small` | `medium` | `full`>',
                                  color=discord.Color.from_rgb(114, 137, 218))

        await ctx.send(embed=embed)

    @commands.command(name='info', aliases=['information'])
    async def info(self, ctx, steam_id):
        pass

    """
    Summary:
        Switch state for the 'profilestate' in the Steam json
    Returns:
        The key/value pair that belongs to the 'profilestate'
    """
    def get_user_state(self, state):
        switch = {
            0: [':red_circle:', 'Offline'],
            1: [':green_circle:', 'Online'],
            2: [':blue_circle:', 'Busy'],
            3: [':orange_circle:', 'Away'],
            4: [':zzz:', 'Snooze'],
            5: [':repeat:', 'Looking to trade'],
            6: [':video_game:', 'Looking to play']
        }

        return switch.get(state, 'Unknown state')

    """
    Summary:
        Switch state for the 'avatar[...]' in the Steam json
    Returns:
        The key/value pair that belongs to the 'avatar[...]'
    """
    def get_avatar_size(self, size):
        switch = {
            'small': '32x32',
            'medium': '64x64',
            'full': '184x184'
        }

        return switch.get(size, 'Unknown size')

    """
    Summary:
        This function gets executed when the Steam ID is not valid
    """
    async def not_valid_steam_id(self, ctx, steam_id):
        embed = discord.Embed(description=f'{ctx.author.mention}, the Steam ID `{steam_id}` is an invalid.',
                              color=discord.Color.from_rgb(114, 137, 218))

        await ctx.send(embed=embed)

    """
    Summary:
        Check if the SteamID is valid
    Returns:
        True is the SteamID is valid, else False
    """
    def is_valid_steam_id(self, steam_id):
        result = send_http_request(f'{self.public_data_url}{steam_id}')
        return len(result['response']['players']) > 0

def setup(client):
    client.add_cog(SteamUser(client))

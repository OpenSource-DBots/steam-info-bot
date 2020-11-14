import asyncio
from datetime import datetime
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


"""
Summary:
    Get the utc from timestamp
Returns:
    Utc from timestamp
"""
def timestamp_to_utc(timestamp):
    time = datetime.utcfromtimestamp(timestamp).strftime('%m/%d/%Y')
    return time


class SteamFriends(commands.Cog):

    # The url to the Steam Web API which has the steam profile data
    user_request_url = f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/' \
                       f'?key={get_json_value(file_path="./confidential-keys.json", key="steam_web_api")}&steamids='

    get_users_from_index = 0
    current_get_users_from_index = 0
    current_page_index = 1
    total_pages = 0

    users_per_page = 7
    previous_page_emoji = '◀️'
    next_page_emoji = '▶️'

    steam_id = ''

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        message = reaction.message

        if str(reaction.emoji) == str(self.previous_page_emoji) and self.current_page_index > 1:
            self.get_users_from_index -= self.users_per_page
            self.current_page_index -= 1
        elif str(reaction.emoji) == str(self.next_page_emoji) and not self.current_page_index > self.total_pages - 1:
            self.get_users_from_index += self.users_per_page
            self.current_page_index += 1

        await message.edit(embed=self.get_new_page(self.steam_id))
        await reaction.remove(user)

    @commands.command(name='friends', aliases=['friends-list', 'friend-list', 'user-friends', 'steam-friends'])
    async def friends(self, ctx, steam_id):
        if not self.is_valid_steam_id(steam_id):
            await self.not_valid_steam_id(ctx, steam_id)
            return

        self.steam_id = steam_id

        loading_message_embed = discord.Embed(
            description=f'Loading `{self.steam_id}`\'s friends list',
            color=discord.Color.from_rgb(114, 137, 218))
        loading_message = await ctx.send(embed=loading_message_embed)

        embed = self.get_new_page(steam_id)

        await loading_message.delete()

        message = await ctx.send(embed=embed)
        await message.add_reaction(emoji=self.previous_page_emoji)
        await message.add_reaction(emoji=self.next_page_emoji)

        # Clear the reactions after 1 minute
        await asyncio.sleep(60)
        await message.clear_reactions()

    def get_new_page(self, steam_id):
        embed = discord.Embed(description=f'**`{steam_id}`\'s Friends List '
                                          f'[Page({self.current_page_index}/{self.calculate_total_pages(steam_id)})]**\n')
        result = send_http_request(self.set_steam_id_in_http_request(steam_id))

        user_on_page_count = 0
        index = -1
        for user in result['friendslist']['friends']:
            index += 1

            if index < self.get_users_from_index:
                continue

            user_on_page_count += 1
            if user_on_page_count <= self.users_per_page:
                user_result = send_http_request(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
                                                f'?key={get_json_value(file_path="./confidential-keys.json", key="steam_web_api")}'
                                                f'&steamids={user["steamid"]}')
                user_result_short = user_result["response"]["players"][0]

                embed.description += f'**{index + 1}:** {self.get_user_state(user_result_short["personastate"])[0]} ' \
                                     f'[*{self.get_user_state(user_result_short["personastate"])[1]}*] ' \
                                     f'[[/id/{user_result_short["steamid"]}/]({user_result_short["profileurl"]})] ' \
                                     f'**{user_result_short["personaname"]}**\n'

        return embed

    """
    Summary:
        Place the Steam ID somewhere in the request link
    Returns:
        Valid link with Steam ID
    """
    def set_steam_id_in_http_request(self, steam_id):
        # The url to the Steam Web API which has the steam profile data
        user_request_url = f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/' \
                           f'?key={get_json_value(file_path="./confidential-keys.json", key="steam_web_api")}' \
                           f'&steamid={steam_id}&relationship=friend'

        return user_request_url

    """
    Summary:
        Calculate the total pages needed for showing each friend
    Returns:
        Total pages count
    """
    def calculate_total_pages(self, steam_id):
        result = send_http_request(self.set_steam_id_in_http_request(steam_id))

        total_pages = 0

        index = 0
        for user in result['friendslist']['friends']:
            index += 1
            if index == self.users_per_page:
                total_pages += 1
                index = 0

        if index > 0:
            total_pages += 1

        self.total_pages = total_pages
        return total_pages

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
        This function gets executed when the Steam ID is not valid
    """
    async def not_valid_steam_id(self, ctx, steam_id):
        embed = discord.Embed(description=f'{ctx.author.mention}, the Steam ID `{steam_id}` is invalid.',
                              color=discord.Color.from_rgb(114, 137, 218))

        await ctx.send(embed=embed)

    """
    Summary:
        Check if the SteamID is valid
    Returns:
        True is the SteamID is valid, else False
    """
    def is_valid_steam_id(self, steam_id):
        result = requests.get(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
                              f'?key={get_json_value(file_path="./confidential-keys.json", key="steam_web_api")}'
                              f'&steamids={steam_id}')
        return result.status_code == 200


def setup(client):
    client.add_cog(SteamFriends(client))

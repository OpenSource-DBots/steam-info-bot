import discord
from discord.ext import commands


class Latency(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(name='ping')
    async def ping(self, ctx):
        embed = discord.Embed(description=f'{ctx.author.mention} :ping_pong: Pong! with '
                                          f'`{round(self.client.latency * 1000)}ms`!',
                              color=discord.Color.from_rgb(114, 137, 218))

        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Latency(client))

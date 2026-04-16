import discord
from discord.ext import commands

ID_CANAL_BOAS_VINDAS = 1493390749142618202 

class Welcome(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        canal = member.guild.get_channel(ID_CANAL_BOAS_VINDAS)
        if canal:
            embed = discord.Embed(
                title="👋 Bem-vindo!", 
                description=f"Olá {member.mention}, diverte-te na Troia!", 
                color=discord.Color.blue()
            )
            await canal.send(embed=embed)

async def setup(bot): 
    await bot.add_cog(Welcome(bot))
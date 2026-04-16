import discord
from discord.ext import commands, tasks
from datetime import datetime

# ID do canal onde o status será postado
ID_CANAL_STATUS = 1493420580450467992

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.atualizar_status.start()

    def cog_unload(self):
        self.atualizar_status.cancel()

    @tasks.loop(minutes=2)
    async def atualizar_status(self):
        canal = self.bot.get_channel(ID_CANAL_STATUS)
        if not canal: 
            return
        
        # Criando um Embed elegante e limpo
        embed = discord.Embed(
            title="🛰️ MONITORAMENTO DE REDE - TROIA RP", 
            description="Confira abaixo as informações de conexão e estado do servidor.",
            color=0x2b2d31 # Cor grafite premium
        )
        
        # Status do Servidor com destaque de cor
        embed.add_field(
            name="🔌 Servidor", 
            value="```diff\n+ ONLINE```", # Texto em verde
            inline=True
        )
        
        # População (Pode ser integrado com API do FiveM futuramente)
        embed.add_field(
            name="👥 Jogadores", 
            value="```Aguardando abertura```", 
            inline=True
        )

        # O Connect IP com formatação de destaque (Estilo Terminal)
        embed.add_field(
            name="🔗 CONEXÃO RÁPIDA (F8)", 
            value="```bash\nconnect em-breve.troiarp.com\n```", # Texto em ciano/azul
            inline=False
        )

        # Adicionando a logo do servidor para identidade visual
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png")
        
        embed.set_footer(
            text=f"Troia RP • Atualizado às {datetime.now().strftime('%H:%M')}",
            icon_url=self.bot.user.display_avatar.url
        )
        
        # Mantém apenas a mensagem mais recente no canal
        try:
            await canal.purge(limit=5)
            await canal.send(embed=embed)
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")

async def setup(bot):
    await bot.add_cog(Status(bot))
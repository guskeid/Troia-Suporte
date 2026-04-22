import discord
from discord.ext import commands, tasks
from datetime import datetime

# ID do canal onde o status será postado
ID_CANAL_STATUS = 1493420580450467992

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mensagem_status = None
        self.atualizar_status.start()

    def cog_unload(self):
        self.atualizar_status.cancel()

    def montar_embed(self):
        embed = discord.Embed(
            title="🛰️ MONITORAMENTO DE REDE - TROIA RP",
            description="Confira abaixo as informações de conexão e estado do servidor.",
            color=0x2b2d31
        )

        embed.add_field(
            name="🔌 Servidor",
            value="```diff\n- MANUTENÇÃO```",
            inline=True
        )

        embed.add_field(
            name="👥 Jogadores",
            value="```Aguardando Inauguração```",
            inline=True
        )

        embed.add_field(
            name="🔗 CONEXÃO RÁPIDA (F8)",
            value="```bash\nconnect em-breve.troiarp.com\n```",
            inline=False
        )

        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png")

        embed.set_footer(
            text=f"Troia RP • Atualizado às {datetime.now().strftime('%H:%M')}",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )
        return embed

    @tasks.loop(minutes=2)
    async def atualizar_status(self):
        canal = self.bot.get_channel(ID_CANAL_STATUS)
        if not canal:
            return

        embed = self.montar_embed()

        try:
            # Se já temos uma mensagem em memória, tenta editar
            if self.mensagem_status:
                try:
                    await self.mensagem_status.edit(embed=embed)
                    return
                except (discord.NotFound, discord.HTTPException):
                    self.mensagem_status = None

            # Procura a última mensagem do bot no canal para reaproveitar
            async for msg in canal.history(limit=10):
                if msg.author == self.bot.user:
                    try:
                        await msg.edit(embed=embed)
                        self.mensagem_status = msg
                        return
                    except (discord.NotFound, discord.HTTPException):
                        continue

            # Se não encontrou nenhuma mensagem do bot, cria uma nova
            self.mensagem_status = await canal.send(embed=embed)
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")

    @atualizar_status.before_loop
    async def antes_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Status(bot))

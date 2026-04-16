import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # Carregar as extensões (Cogs)
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Módulo {filename} carregado.')
                except Exception as e:
                    print(f'❌ Erro ao carregar {filename}: {e}')
        
        # Importar views para persistência
        from cogs.tickets import TicketView, ConfirmCloseView
        from cogs.whitelist import WhitelistView
        from cogs.verificacao import VerificacaoView
        
        # Adicionar Views persistentes (para os botões não pararem de funcionar)
        self.add_view(TicketView(self))
        self.add_view(ConfirmCloseView(self))
        self.add_view(WhitelistView())
        self.add_view(VerificacaoView())
        
        await self.tree.sync()
        print("✅ Comandos de barra sincronizados.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'--- {bot.user} ESTÁ ONLINE ---')

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERRO: DISCORD_TOKEN não encontrado no .env")
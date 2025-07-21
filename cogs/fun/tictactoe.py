# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Import
# ───────────────────────────────────────────────
from discord.ui import Button, View
from FastCoding.backend import discord, commands, ezcord
# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=x)
        self.x = x
        self.y = y
        self.clicked = False

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user != view.current_player:
            await interaction.response.send_message("Du bist gerade nicht dran!", ephemeral=True)
            return
        if self.clicked:
            await interaction.response.send_message("Dieses Feld ist schon belegt!", ephemeral=True)
            return

        self.clicked = True
        if view.current_turn == 0:
            self.style = discord.ButtonStyle.danger  # rot = X
            self.label = "X"
            view.board[self.x][self.y] = "X"
            view.current_turn = 1
            view.current_player = view.player2
        else:
            self.style = discord.ButtonStyle.success  # grün = O
            self.label = "O"
            view.board[self.x][self.y] = "O"
            view.current_turn = 0
            view.current_player = view.player1

        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"Spiel vorbei! {winner} hat gewonnen!", view=view)
            view.stop()
        elif view.is_draw():
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content="Unentschieden!", view=view)
            view.stop()
        else:
            await interaction.response.edit_message(content=f"Jetzt ist {view.current_player.mention} dran!", view=view)

class TicTacToeView(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=120)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_turn = 0  # 0 = X (player1), 1 = O (player2)
        self.board = [["" for _ in range(3)] for _ in range(3)]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        b = self.board
        players_map = {"X": self.player1, "O": self.player2}
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != "":
                winner_symbol = b[i][0]
                return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        for i in range(3):
            if b[0][i] == b[1][i] == b[2][i] != "":
                winner_symbol = b[0][i]
                return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        if b[0][0] == b[1][1] == b[2][2] != "":
            winner_symbol = b[0][0]
            return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        if b[0][2] == b[1][1] == b[2][0] != "":
            winner_symbol = b[0][2]
            return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        return None

    def is_draw(self):
        return all(cell != "" for row in self.board for cell in row)

class fun(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="tictactoe", description="Starte ein Tic Tac Toe Spiel mit jemandem!")
    async def tictactoe(self, ctx: discord.ApplicationContext, opponent: discord.Member):
        if opponent.bot:
            await ctx.respond("Du kannst nicht gegen einen Bot spielen!", ephemeral=True)
            return
        if opponent == ctx.author:
            await ctx.respond("Du kannst nicht gegen dich selbst spielen!", ephemeral=True)
            return

        view = TicTacToeView(ctx.author, opponent)
        await ctx.respond(f"Tic Tac Toe: {ctx.author.mention} (X) gegen {opponent.mention} (O)\n{ctx.author.mention} fängt an!", view=view)

def setup(bot):
    bot.add_cog(fun(bot))

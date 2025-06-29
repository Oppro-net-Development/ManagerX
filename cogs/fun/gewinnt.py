# ───────────────────────────────────────────────
# >> Import
# ───────────────────────────────────────────────
from discord.ui import Button, View
from FastCoding.backend import discord, commands, ezcord

# ───────────────────────────────────────────────
# >> Cogs
# ───────────────────────────────────────────────
ROWS = 6
COLUMNS = 7

class Connect4Button(Button):
    def __init__(self, column):
        super().__init__(style=discord.ButtonStyle.secondary, label=str(column + 1))
        self.column = column

    async def callback(self, interaction: discord.Interaction):
        view: Connect4View = self.view
        if interaction.user != view.current_player:
            await interaction.response.send_message("Du bist gerade nicht dran!", ephemeral=True)
            return

        if not view.make_move(self.column):
            await interaction.response.send_message("Diese Spalte ist voll!", ephemeral=True)
            return

        winner = view.check_winner()
        board_str = view.board_to_str()
        if winner:
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"Spiel vorbei! {winner} hat gewonnen!\n\n{board_str}", view=view)
            view.stop()
            return
        elif view.is_draw():
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"Unentschieden!\n\n{board_str}", view=view)
            view.stop()
            return

        view.switch_player()
        await interaction.response.edit_message(content=f"Jetzt ist {view.current_player.mention} dran!\n\n{board_str}", view=view)

class Connect4View(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_symbol = "🔴"  # Player 1
        self.board = [["⚪" for _ in range(COLUMNS)] for _ in range(ROWS)]

        for col in range(COLUMNS):
            self.add_item(Connect4Button(col))

    def make_move(self, column):
        # Platziere das Symbol in der niedrigsten freien Zeile in der Spalte
        for row in reversed(range(ROWS)):
            if self.board[row][column] == "⚪":
                self.board[row][column] = self.current_symbol
                return True
        return False

    def switch_player(self):
        if self.current_player == self.player1:
            self.current_player = self.player2
            self.current_symbol = "🟡"  # Player 2
        else:
            self.current_player = self.player1
            self.current_symbol = "🔴"  # Player 1

    def check_winner(self):
        b = self.board
        # Prüfe horizontal
        for row in range(ROWS):
            for col in range(COLUMNS - 3):
                line = b[row][col:col+4]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return f"{line[0]} {self.current_player.mention}"

        # Prüfe vertikal
        for col in range(COLUMNS):
            for row in range(ROWS - 3):
                line = [b[row+i][col] for i in range(4)]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return f"{line[0]} {self.current_player.mention}"

        # Prüfe diagonal (rechts unten)
        for row in range(ROWS - 3):
            for col in range(COLUMNS - 3):
                line = [b[row+i][col+i] for i in range(4)]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return f"{line[0]} {self.current_player.mention}"

        # Prüfe diagonal (rechts oben)
        for row in range(3, ROWS):
            for col in range(COLUMNS - 3):
                line = [b[row-i][col+i] for i in range(4)]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return f"{line[0]} {self.current_player.mention}"

        return None

    def is_draw(self):
        return all(cell != "⚪" for row in self.board for cell in row)

    def board_to_str(self):
        return "\n".join("".join(row) for row in self.board)

class Connect4Cog(ezcord.Cog, group="fun"):
    @commands.slash_command(name="connect4", description="Starte ein 4 Gewinnt Spiel mit jemandem!")
    async def connect4(self, ctx: discord.ApplicationContext, opponent: discord.Member):
        if opponent.bot:
            await ctx.respond("Du kannst nicht gegen einen Bot spielen!", ephemeral=True)
            return
        if opponent == ctx.author:
            await ctx.respond("Du kannst nicht gegen dich selbst spielen!", ephemeral=True)
            return

        view = Connect4View(ctx.author, opponent)
        await ctx.respond(
            f"4 Gewinnt: {ctx.author.mention} (🔴) vs {opponent.mention} (🟡)\n{ctx.author.mention} fängt an!\n\n" + view.board_to_str(),
            view=view
        )

def setup(bot):
    bot.add_cog(Connect4Cog(bot))

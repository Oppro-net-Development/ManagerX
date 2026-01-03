# Copyright (c) 2025 OPPRO.NET Network
# ───────────────────────────────────────────────
# >> Import
# ───────────────────────────────────────────────
from discord.ui import Button, View
import discord
from discord.ext import commands
import ezcord
import yaml
from pathlib import Path

# ───────────────────────────────────────────────
# >> Constants
# ───────────────────────────────────────────────
ROWS = 6
COLUMNS = 7

# ───────────────────────────────────────────────
# >> Load messages from YAML
# ───────────────────────────────────────────────
def load_messages(lang_code: str):
    """
    Lädt Nachrichten für den angegebenen Sprachcode.
    Fällt auf 'en' und dann auf 'de' zurück, falls die Datei fehlt.
    """
    base_path = Path("translation") / "messages"
    
    # 1. Versuch: Gewünschte Sprache
    lang_file = base_path / f"{lang_code}.yaml"
    
    # 2. Versuch: Standard (Englisch)
    if not lang_file.exists():
        lang_file = base_path / "en.yaml"

    # 3. Versuch: Fallback (Deutsch)
    if not lang_file.exists():
        lang_file = base_path / "de.yaml"
    
    # Kritischer Fehler, wenn keine der drei Dateien existiert
    if not lang_file.exists():
        raise FileNotFoundError(f"Missing language files: {lang_code}.yaml, en.yaml, and de.yaml")

    with open(lang_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ───────────────────────────────────────────────
# >> Button & View
# ───────────────────────────────────────────────
class Connect4Button(Button):
    def __init__(self, column, view):
        super().__init__(style=discord.ButtonStyle.secondary, label=str(column + 1))
        self.column = column
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        msgs = view.messages

        if interaction.user != view.current_player:
            await interaction.response.send_message(
                msgs["cog_4gewinnt"]["error_types"]["not_your_turn"],
                ephemeral=True
            )
            return

        if not view.make_move(self.column):
            await interaction.response.send_message(
                msgs["cog_4gewinnt"]["error_types"]["this_column_full"],
                ephemeral=True
            )
            return

        winner = view.check_winner()
        board_str = view.board_to_str()
        
        if winner or view.is_draw():
            for child in view.children:
                child.disabled = True
            
            content = ""
            if winner:
                content = msgs["cog_4gewinnt"]["win_types"]["win"].format(
                    winner=view.current_player.mention,
                    board_str=board_str
                )
            elif view.is_draw():
                content = msgs["cog_4gewinnt"]["win_types"]["draw"].format(
                    board_str=board_str
                )
            
            await interaction.response.edit_message(
                content=content,
                view=view
            )
            view.stop()
            return

        view.switch_player()
        await interaction.response.edit_message(
            content=msgs["cog_4gewinnt"]["message"]["player_turn"].format(
                view=view,
                board_str=board_str
            ),
            view=view
        )

class Connect4View(View):
    def __init__(self, player1, player2, messages):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_symbol = "🔴"
        self.board = [["⚪" for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.messages = messages

        for col in range(COLUMNS):
            self.add_item(Connect4Button(col, self))

    def make_move(self, column):
        for row in reversed(range(ROWS)):
            if self.board[row][column] == "⚪":
                self.board[row][column] = self.current_symbol
                return True
        return False

    def switch_player(self):
        if self.current_player == self.player1:
            self.current_player = self.player2
            self.current_symbol = "🟡"
        else:
            self.current_player = self.player1
            self.current_symbol = "🔴"

    def check_winner(self):
        b = self.board
        # horizontal
        for row in range(ROWS):
            for col in range(COLUMNS - 3):
                line = b[row][col:col+4]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return True
        # vertikal
        for col in range(COLUMNS):
            for row in range(ROWS - 3):
                line = [b[row+i][col] for i in range(4)]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return True
        # diagonal rechts unten
        for row in range(ROWS - 3):
            for col in range(COLUMNS - 3):
                line = [b[row+i][col+i] for i in range(4)]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return True
        # diagonal rechts oben
        for row in range(3, ROWS):
            for col in range(COLUMNS - 3):
                line = [b[row-i][col+i] for i in range(4)]
                if line.count(line[0]) == 4 and line[0] != "⚪":
                    return True
        return None

    def is_draw(self):
        return all(cell != "⚪" for row in self.board for cell in row)

    def board_to_str(self):
        return "\n".join("".join(row) for row in self.board)


# ───────────────────────────────────────────────
# >> Cog
# ───────────────────────────────────────────────
class Connect4Cog(ezcord.Cog, group="fun"):
    @commands.slash_command(name="connect4", description="Starte ein 4 Gewinnt Spiel mit jemandem!")
    async def connect4(self, ctx: discord.ApplicationContext, opponent: discord.Member):
        
        try:
            lang_code = self.bot.get_user_language(ctx.author.id)
        except AttributeError:
            lang_code = "de"
        
        try:
            messages = load_messages(lang_code)
        except FileNotFoundError as e:
            print(f"CRITICAL: {e}")
            messages = {"cog_4gewinnt": {"error_types": {"is_opponent_bot": "Error: Missing language file."}, 
                                         "message": {"start_game": "Error: Missing language file."}}}

        if opponent.bot:
            await ctx.respond(
                messages["cog_4gewinnt"]["error_types"]["is_opponent_bot"],
                ephemeral=True
            )
            return
        if opponent == ctx.author:
            await ctx.respond(
                messages["cog_4gewinnt"]["error_types"]["is_opponent_self"],
                ephemeral=True
            )
            return

        view = Connect4View(ctx.author, opponent, messages)
        
        # 🟢 KORREKTUR: Stabile Formatierung
        await ctx.respond(
            messages["cog_4gewinnt"]["message"]["start_game"].format(
                author_mention=ctx.author.mention,
                opponent_mention=opponent.mention
            ) + view.board_to_str(),
            view=view
        )

def setup(bot):
    bot.add_cog(Connect4Cog(bot))
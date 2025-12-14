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
# >> Hilfsfunktionen
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
        # Da dies nur beim Laden eines Commands passiert, keine exit() nötig
        print(f"WARNUNG: Keine Sprachdatei für '{lang_code}' gefunden. Verwende leere Texte.")
        return {} 

    with open(lang_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 🔴 ENTFERNT: Die globale 'messages' Variable wird entfernt.
# Die Nachrichten werden jetzt in der Cog-Methode geladen.


class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=x)
        self.x = x
        self.y = y
        self.clicked = False
        # Speichere die Nachrichten direkt im Button für den Callback
        # Siehe Callback: messages werden aus der View geholt

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        messages = view.messages # 🌟 NEU: Nachrichten aus der View abrufen

        # 🟢 Korrigierte i18n-Nutzung: Nicht dein Zug
        if interaction.user != view.current_player:
            await interaction.response.send_message(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("not_your_turn", "Not your turn!"), 
                ephemeral=True
            )
            return
            
        # 🟢 Korrigierte i18n-Nutzung: Feld belegt
        if self.clicked:
            await interaction.response.send_message(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("this_cell_taken", "This cell is already taken!"), 
                ephemeral=True
            )
            return

        # ... (Spiellogik bleibt gleich) ...
        self.clicked = True
        if view.current_turn == 0:
            self.style = discord.ButtonStyle.danger # rot = X
            self.label = "X"
            view.board[self.x][self.y] = "X"
            view.current_turn = 1
            view.current_player = view.player2
        else:
            self.style = discord.ButtonStyle.success # grün = O
            self.label = "O"
            view.board[self.x][self.y] = "O"
            view.current_turn = 0
            view.current_player = view.player1

        winner = view.check_winner()
        
        if winner:
            for child in view.children:
                child.disabled = True
            
            # 🟢 Korrigierte i18n-Nutzung: Gewinn
            win_msg = messages.get("cog_tictactoe", {}).get("win_types", {}).get("win", "WINNER: {winner}").format(winner=winner)
            await interaction.response.edit_message(content=win_msg, view=view)
            view.stop()
            
        elif view.is_draw():
            for child in view.children:
                child.disabled = True
            
            # 🟢 Korrigierte i18n-Nutzung: Unentschieden
            draw_msg = messages.get("cog_tictactoe", {}).get("win_types", {}).get("draw", "It's a draw!")
            await interaction.response.edit_message(content=draw_msg, view=view)
            view.stop()
        
        else:
            # 🌟 NEU: I18N für den Zugwechsel
            next_turn_msg = messages.get("cog_tictactoe", {}).get("message", {}).get("next_turn", "It is now {player}'s turn!").format(
                player=view.current_player.mention
            )
            await interaction.response.edit_message(content=next_turn_msg, view=view)

class TicTacToeView(View):
    def __init__(self, player1, player2, messages): # 🌟 NEU: Nachrichten werden übergeben
        super().__init__(timeout=120)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_turn = 0 # 0 = X (player1), 1 = O (player2)
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.messages = messages # 🌟 NEU: Nachrichten werden hier gespeichert
        
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    # check_winner und is_draw bleiben unverändert
    def check_winner(self):
        # ... (Ihre bestehende Logik) ...
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
        
        # 🌟 NEU: Rufe den Sprachcode aus der Datenbank ab
        # Annahme: Ihre db-Methode ist get_user_language
        lang_code = self.bot.settings_db.get_user_language(ctx.author.id)
        
        # 🌟 NEU: Lade die korrekten Nachrichten für den Benutzer
        messages = load_messages(lang_code)

        # 🟢 Korrigierte i18n-Nutzung: Gegner ist Bot
        if opponent.bot:
            await ctx.respond(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("is_opponent_bot", "You cannot challenge a bot."), 
                ephemeral=True
            )
            return
            
        # 🟢 Korrigierte i18n-Nutzung: Gegner ist man selbst
        if opponent == ctx.author:
            await ctx.respond(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("is_opponent_self", "You cannot challenge yourself."), 
                ephemeral=True
            )
            return

        # 🌟 NEU: Übergebe Nachrichten an die View
        view = TicTacToeView(ctx.author, opponent, messages)
        
        # 🟢 KORREKTUR: Stabile Formatierung zur Behebung des Hängens während der Synchronisierung.
        start_msg = messages.get("cog_tictactoe", {}).get("message", {}).get("start_game", "Tic Tac Toe: {author_mention} vs {opponent_mention}").format(
            author_mention=ctx.author.mention,
            opponent_mention=opponent.mention
        )
        await ctx.respond(start_msg, view=view)

def setup(bot):
    bot.add_cog(fun(bot))
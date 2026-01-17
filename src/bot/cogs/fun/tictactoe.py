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
from typing import Optional, List, Tuple
import asyncio
import random

# ───────────────────────────────────────────────
# >> Constants
# ───────────────────────────────────────────────
DEFAULT_TIMEOUT = 120

DIFFICULTY_CONFIG = {
    "easy": {
        "name": "Anfänger",
        "randomness": 0.5  # 50% zufällige Züge
    },
    "medium": {
        "name": "Fortgeschritten",
        "randomness": 0.2  # 20% zufällige Züge
    },
    "hard": {
        "name": "Experte",
        "randomness": 0.0  # Perfektes Spiel
    }
}

# ───────────────────────────────────────────────
# >> Statistics Manager
# ───────────────────────────────────────────────
class GameStats:
    """Verwaltet Spielstatistiken für TicTacToe"""
    
    def __init__(self):
        self.stats = {}
    
    def get_user_stats(self, user_id: int) -> dict:
        if user_id not in self.stats:
            self.stats[user_id] = {
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "total_games": 0,
                "win_streak": 0,
                "best_streak": 0,
                "ai_wins": 0,
                "ai_losses": 0
            }
        return self.stats[user_id]
    
    def record_win(self, user_id: int, vs_ai: bool = False):
        stats = self.get_user_stats(user_id)
        stats["wins"] += 1
        stats["total_games"] += 1
        stats["win_streak"] += 1
        stats["best_streak"] = max(stats["best_streak"], stats["win_streak"])
        if vs_ai:
            stats["ai_wins"] += 1
    
    def record_loss(self, user_id: int, vs_ai: bool = False):
        stats = self.get_user_stats(user_id)
        stats["losses"] += 1
        stats["total_games"] += 1
        stats["win_streak"] = 0
        if vs_ai:
            stats["ai_losses"] += 1
    
    def record_draw(self, user_id: int):
        stats = self.get_user_stats(user_id)
        stats["draws"] += 1
        stats["total_games"] += 1
        stats["win_streak"] = 0
    
    def get_winrate(self, user_id: int) -> float:
        stats = self.get_user_stats(user_id)
        if stats["total_games"] == 0:
            return 0.0
        return (stats["wins"] / stats["total_games"]) * 100

# Global stats instance
game_stats = GameStats()

# ───────────────────────────────────────────────
# >> Load messages from YAML
# ───────────────────────────────────────────────
def load_messages(lang_code: str):
    """
    Lädt Nachrichten für den angegebenen Sprachcode.
    Fällt auf 'en' und dann auf 'de' zurück, falls die Datei fehlt.
    """
    base_path = Path("translation") / "messages"
    
    lang_file = base_path / f"{lang_code}.yaml"
    if not lang_file.exists():
        lang_file = base_path / "en.yaml"
    if not lang_file.exists():
        lang_file = base_path / "de.yaml"
    
    if not lang_file.exists():
        print(f"WARNUNG: Keine Sprachdatei für '{lang_code}' gefunden. Verwende leere Texte.")
        return {}

    with open(lang_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ───────────────────────────────────────────────
# >> AI Engine (Minimax Algorithm)
# ───────────────────────────────────────────────
class TicTacToeAI:
    """KI-Gegner mit Minimax-Algorithmus für TicTacToe"""
    
    def __init__(self, difficulty: str = "medium"):
        config = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])
        self.randomness = config["randomness"]
        self.difficulty_name = config["name"]
    
    def get_available_moves(self, board: List[List[str]]) -> List[Tuple[int, int]]:
        """Gibt alle verfügbaren Züge zurück"""
        moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == "":
                    moves.append((i, j))
        return moves
    
    def check_winner(self, board: List[List[str]]) -> Optional[str]:
        """Prüft ob es einen Gewinner gibt"""
        # Horizontal
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] != "":
                return board[i][0]
        
        # Vertikal
        for i in range(3):
            if board[0][i] == board[1][i] == board[2][i] != "":
                return board[0][i]
        
        # Diagonal
        if board[0][0] == board[1][1] == board[2][2] != "":
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != "":
            return board[0][2]
        
        return None
    
    def is_board_full(self, board: List[List[str]]) -> bool:
        """Prüft ob das Board voll ist"""
        return all(cell != "" for row in board for cell in row)
    
    def minimax(self, board: List[List[str]], depth: int, is_maximizing: bool, 
                ai_symbol: str, player_symbol: str) -> int:
        """Minimax-Algorithmus für optimale Züge"""
        winner = self.check_winner(board)
        
        # Terminal-Zustände
        if winner == ai_symbol:
            return 10 - depth  # Schnellerer Gewinn ist besser
        elif winner == player_symbol:
            return depth - 10  # Schnellerer Verlust ist schlechter
        elif self.is_board_full(board):
            return 0  # Unentschieden
        
        if is_maximizing:
            best_score = float('-inf')
            for i, j in self.get_available_moves(board):
                board[i][j] = ai_symbol
                score = self.minimax(board, depth + 1, False, ai_symbol, player_symbol)
                board[i][j] = ""
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i, j in self.get_available_moves(board):
                board[i][j] = player_symbol
                score = self.minimax(board, depth + 1, True, ai_symbol, player_symbol)
                board[i][j] = ""
                best_score = min(score, best_score)
            return best_score
    
    def get_best_move(self, board: List[List[str]], ai_symbol: str, player_symbol: str) -> Tuple[int, int]:
        """Gibt den besten Zug zurück"""
        available_moves = self.get_available_moves(board)
        
        if not available_moves:
            return (0, 0)
        
        # Zufälligkeit für niedrigere Schwierigkeitsgrade
        if random.random() < self.randomness:
            return random.choice(available_moves)
        
        # Prüfe auf Gewinnzug
        for i, j in available_moves:
            board[i][j] = ai_symbol
            if self.check_winner(board) == ai_symbol:
                board[i][j] = ""
                return (i, j)
            board[i][j] = ""
        
        # Prüfe ob Gegner blockiert werden muss
        for i, j in available_moves:
            board[i][j] = player_symbol
            if self.check_winner(board) == player_symbol:
                board[i][j] = ""
                return (i, j)
            board[i][j] = ""
        
        # Verwende Minimax für optimalen Zug
        best_score = float('-inf')
        best_move = available_moves[0]
        
        for i, j in available_moves:
            board[i][j] = ai_symbol
            score = self.minimax(board, 0, False, ai_symbol, player_symbol)
            board[i][j] = ""
            
            if score > best_score:
                best_score = score
                best_move = (i, j)
        
        return best_move

# ───────────────────────────────────────────────
# >> Enhanced Button & View
# ───────────────────────────────────────────────
class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=x)
        self.x = x
        self.y = y
        self.clicked = False

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        messages = view.messages

        # Prüfe ob Spiel bereits beendet
        if view.game_ended:
            await interaction.response.send_message(
                "Das Spiel ist bereits beendet!",
                ephemeral=True
            )
            return

        # PvP mode checks
        if not view.is_ai_mode and interaction.user != view.current_player:
            await interaction.response.send_message(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("not_your_turn", "Not your turn!"), 
                ephemeral=True
            )
            return
        
        # AI mode checks
        if view.is_ai_mode and interaction.user != view.player1:
            await interaction.response.send_message(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("not_your_turn", "Not your turn!"), 
                ephemeral=True
            )
            return
            
        if self.clicked:
            await interaction.response.send_message(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("this_cell_taken", "This cell is already taken!"), 
                ephemeral=True
            )
            return

        # Spieler-Zug
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
            await view.end_game(interaction, winner)
            return
            
        elif view.is_draw():
            await view.end_game(interaction, None)
            return
        
        # AI-Zug
        if view.is_ai_mode and view.current_player == view.player2:
            next_turn_msg = messages.get("cog_tictactoe", {}).get("message", {}).get("ai_thinking", "🤖 KI denkt nach...").format(
                player=view.current_player.mention
            )
            await interaction.response.edit_message(content=next_turn_msg, view=view)
            
            # Simuliere Denkzeit
            await asyncio.sleep(0.8)
            
            # KI macht Zug
            ai_move = view.ai.get_best_move(view.board, "O", "X")
            if ai_move:
                ai_x, ai_y = ai_move
                for child in view.children:
                    if isinstance(child, TicTacToeButton) and child.x == ai_x and child.y == ai_y:
                        child.clicked = True
                        child.style = discord.ButtonStyle.success
                        child.label = "O"
                        view.board[ai_x][ai_y] = "O"
                        view.current_turn = 0
                        view.current_player = view.player1
                        break
                
                winner = view.check_winner()
                
                if winner:
                    await view.end_game(interaction, winner, is_followup=True)
                    return
                    
                elif view.is_draw():
                    await view.end_game(interaction, None, is_followup=True)
                    return
                
                # Zeige KI-Zug an
                next_turn_msg = messages.get("cog_tictactoe", {}).get("message", {}).get("ai_moved", "✅ KI hat Feld ({x}, {y}) gewählt!\n\n{player}, du bist dran!").format(
                    x=ai_x + 1,
                    y=ai_y + 1,
                    player=view.current_player.mention
                )
                await interaction.edit_original_response(content=next_turn_msg, view=view)
        else:
            next_turn_msg = messages.get("cog_tictactoe", {}).get("message", {}).get("next_turn", "It is now {player}'s turn!").format(
                player=view.current_player.mention
            )
            await interaction.response.edit_message(content=next_turn_msg, view=view)

class TicTacToeView(View):
    def __init__(self, player1, player2, messages, is_ai_mode=False, difficulty="medium"):
        super().__init__(timeout=DEFAULT_TIMEOUT)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_turn = 0  # 0 = X (player1), 1 = O (player2)
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.messages = messages
        self.is_ai_mode = is_ai_mode
        self.difficulty = difficulty
        self.ai = TicTacToeAI(difficulty) if is_ai_mode else None
        self.game_ended = False
        
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        """Prüft auf Gewinner"""
        b = self.board
        players_map = {"X": self.player1, "O": self.player2}
        
        # Horizontal
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != "":
                winner_symbol = b[i][0]
                return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        
        # Vertikal
        for i in range(3):
            if b[0][i] == b[1][i] == b[2][i] != "":
                winner_symbol = b[0][i]
                return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        
        # Diagonal
        if b[0][0] == b[1][1] == b[2][2] != "":
            winner_symbol = b[0][0]
            return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        if b[0][2] == b[1][1] == b[2][0] != "":
            winner_symbol = b[0][2]
            return f"{winner_symbol} ({players_map[winner_symbol].display_name})"
        
        return None

    def is_draw(self):
        """Prüft auf Unentschieden"""
        return all(cell != "" for row in self.board for cell in row)
    
    async def end_game(self, interaction: discord.Interaction, winner: Optional[str], is_followup: bool = False):
        """Beendet das Spiel und zeigt Statistiken"""
        self.game_ended = True
        
        for child in self.children:
            child.disabled = True
        
        messages = self.messages
        
        # Update Statistiken
        if winner:
            winner_symbol = winner[0]  # "X" oder "O"
            winner_player = self.player1 if winner_symbol == "X" else self.player2
            loser_player = self.player2 if winner_symbol == "X" else self.player1
            
            if self.is_ai_mode:
                if winner_player == self.player1:
                    game_stats.record_win(self.player1.id, vs_ai=True)
                else:
                    game_stats.record_loss(self.player1.id, vs_ai=True)
            else:
                game_stats.record_win(winner_player.id)
                game_stats.record_loss(loser_player.id)
        else:
            game_stats.record_draw(self.player1.id)
            if not self.is_ai_mode:
                game_stats.record_draw(self.player2.id)
        
        # Erstelle Embed
        embed = discord.Embed(
            title="🎮 Tic Tac Toe - Spiel beendet!",
            color=discord.Color.green() if winner else discord.Color.gold()
        )
        
        # Ergebnis
        if winner:
            if self.is_ai_mode and winner[0] == "O":
                result_text = f"🤖 **Die {self.ai.difficulty_name} KI hat gewonnen!**"
                embed.color = discord.Color.red()
            else:
                result_text = messages.get("cog_tictactoe", {}).get("win_types", {}).get("win", "WINNER: {winner}").format(winner=winner)
        else:
            result_text = messages.get("cog_tictactoe", {}).get("win_types", {}).get("draw", "It's a draw!")
        
        embed.add_field(
            name="🎯 Ergebnis",
            value=result_text,
            inline=False
        )
        
        # Statistiken
        if winner:
            winner_player = self.player1 if winner[0] == "X" else self.player2
            if not self.is_ai_mode or winner_player == self.player1:
                stats = game_stats.get_user_stats(winner_player.id)
                
                if self.is_ai_mode:
                    stats_text = f"🏆 Siege vs KI: {stats['ai_wins']}\n💔 Niederlagen vs KI: {stats['ai_losses']}\n🔥 Serie: {stats['win_streak']}"
                else:
                    stats_text = f"🏆 Siege: {stats['wins']}\n💔 Niederlagen: {stats['losses']}\n🔥 Serie: {stats['win_streak']}"
                
                embed.add_field(
                    name="📈 Spieler-Stats",
                    value=stats_text,
                    inline=True
                )
        
        # Spielfeld anzeigen
        board_display = ""
        for row in self.board:
            board_display += " | ".join([cell if cell else "·" for cell in row]) + "\n"
        
        embed.add_field(
            name="🎲 Endposition",
            value=f"```\n{board_display}```",
            inline=False
        )
        
        embed.set_footer(text=f"Schwierigkeit: {self.ai.difficulty_name if self.is_ai_mode else 'PvP'}")
        
        if is_followup:
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)
        
        self.stop()
    
    async def on_timeout(self):
        """Wird aufgerufen wenn das Timeout erreicht wird"""
        self.game_ended = True
        for child in self.children:
            child.disabled = True

# ───────────────────────────────────────────────
# >> Cog
# ───────────────────────────────────────────────
class fun(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="tictactoe", description="Starte ein Tic Tac Toe Spiel!")
    async def tictactoe(
        self, 
        ctx: discord.ApplicationContext, 
        opponent: Optional[discord.Member] = None,
        difficulty: discord.Option(
            str,
            description="KI-Schwierigkeit (nur wenn kein Gegner gewählt)",
            choices=["easy", "medium", "hard"],
            default="medium",
            required=False
        ) = "medium"
    ):
        try:
            lang_code = self.bot.settings_db.get_user_language(ctx.author.id)
        except:
            lang_code = "de"
        
        messages = load_messages(lang_code)

        # AI mode
        if opponent is None:
            ai_user = ctx.guild.me
            view = TicTacToeView(ctx.author, ai_user, messages, is_ai_mode=True, difficulty=difficulty)
            
            difficulty_info = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])
            difficulty_emoji = {"easy": "😊", "medium": "🤔", "hard": "😈"}
            
            await ctx.respond(
                f"🤖 **Tic Tac Toe vs KI** {difficulty_emoji.get(difficulty, '🤖')}\n"
                f"**Schwierigkeit:** {difficulty_info['name']}\n"
                f"{ctx.author.mention} (X) spielt gegen die KI! (O)\n\n"
                f"Du bist dran!",
                view=view
            )
            return

        # PvP mode validations
        if opponent.bot:
            await ctx.respond(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("is_opponent_bot", "You cannot challenge a bot."), 
                ephemeral=True
            )
            return
            
        if opponent == ctx.author:
            await ctx.respond(
                messages.get("cog_tictactoe", {}).get("error_types", {}).get("is_opponent_self", "You cannot challenge yourself."), 
                ephemeral=True
            )
            return

        view = TicTacToeView(ctx.author, opponent, messages)
        
        start_msg = messages.get("cog_tictactoe", {}).get("message", {}).get("start_game", "Tic Tac Toe: {author_mention} vs {opponent_mention}").format(
            author_mention=ctx.author.mention,
            opponent_mention=opponent.mention
        )
        await ctx.respond(start_msg, view=view)
    
    @commands.slash_command(name="tictactoestats", description="Zeige deine Tic Tac Toe Statistiken!")
    async def stats(self, ctx: discord.ApplicationContext, user: Optional[discord.Member] = None):
        target_user = user or ctx.author
        stats = game_stats.get_user_stats(target_user.id)
        winrate = game_stats.get_winrate(target_user.id)
        
        embed = discord.Embed(
            title=f"📊 Tic Tac Toe Statistiken - {target_user.display_name}",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.add_field(
            name="🎯 Übersicht",
            value=f"**Gesamt:** {stats['total_games']}\n"
                  f"🏆 Siege: {stats['wins']}\n"
                  f"💔 Niederlagen: {stats['losses']}\n"
                  f"🤝 Unentschieden: {stats['draws']}",
            inline=True
        )
        
        embed.add_field(
            name="📈 Performance",
            value=f"**Siegrate:** {winrate:.1f}%\n"
                  f"🔥 Aktuelle Serie: {stats['win_streak']}\n"
                  f"⭐ Beste Serie: {stats['best_streak']}",
            inline=True
        )
        
        # KI-Stats
        if stats['ai_wins'] > 0 or stats['ai_losses'] > 0:
            ai_total = stats['ai_wins'] + stats['ai_losses']
            ai_winrate = (stats['ai_wins'] / ai_total * 100) if ai_total > 0 else 0
            embed.add_field(
                name="🤖 KI-Statistiken",
                value=f"🏆 Siege: {stats['ai_wins']}\n"
                      f"💔 Niederlagen: {stats['ai_losses']}\n"
                      f"📊 Siegrate: {ai_winrate:.1f}%",
                inline=True
            )
        
        embed.set_footer(text=f"Abgefragt von {ctx.author.display_name}")
        
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(fun(bot))
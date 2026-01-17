# Copyright (c) 2026 ManagerX Development
# ───────────────────────────────────────────────
# >> Import
# ───────────────────────────────────────────────
from discord.ui import Button, View, Select
import discord
from discord.ext import commands
import ezcord
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import asyncio
import random

# ───────────────────────────────────────────────
# >> Constants
# ───────────────────────────────────────────────
ROWS = 6
COLUMNS = 7
DEFAULT_TIMEOUT = 300  # 5 Minuten

# Improved difficulty levels with better depth and strategy
DIFFICULTY_CONFIG = {
    "easy": {
        "depth": 2,
        "randomness": 0.3,  # 30% zufällige Züge
        "name": "Anfänger"
    },
    "medium": {
        "depth": 4,
        "randomness": 0.1,  # 10% zufällige Züge
        "name": "Fortgeschritten"
    },
    "hard": {
        "depth": 6,
        "randomness": 0.0,  # Keine zufälligen Züge
        "name": "Experte"
    }
}

# ───────────────────────────────────────────────
# >> Statistics Manager
# ───────────────────────────────────────────────
class GameStats:
    """Verwaltet Spielstatistiken für Connect4"""
    
    def __init__(self):
        self.stats: Dict[int, Dict] = {}
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Gibt Statistiken für einen Benutzer zurück"""
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
        """Zeichnet einen Sieg auf"""
        stats = self.get_user_stats(user_id)
        stats["wins"] += 1
        stats["total_games"] += 1
        stats["win_streak"] += 1
        stats["best_streak"] = max(stats["best_streak"], stats["win_streak"])
        if vs_ai:
            stats["ai_wins"] += 1
    
    def record_loss(self, user_id: int, vs_ai: bool = False):
        """Zeichnet eine Niederlage auf"""
        stats = self.get_user_stats(user_id)
        stats["losses"] += 1
        stats["total_games"] += 1
        stats["win_streak"] = 0
        if vs_ai:
            stats["ai_losses"] += 1
    
    def record_draw(self, user_id: int):
        """Zeichnet ein Unentschieden auf"""
        stats = self.get_user_stats(user_id)
        stats["draws"] += 1
        stats["total_games"] += 1
        stats["win_streak"] = 0
    
    def get_winrate(self, user_id: int) -> float:
        """Berechnet die Gewinnrate"""
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
        raise FileNotFoundError(f"Missing language files: {lang_code}.yaml, en.yaml, and de.yaml")

    with open(lang_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ───────────────────────────────────────────────
# >> Enhanced AI Engine (Improved Minimax)
# ───────────────────────────────────────────────
class Connect4AI:
    """Verbesserte KI mit optimiertem Minimax-Algorithmus"""
    
    def __init__(self, difficulty: str = "medium"):
        config = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])
        self.max_depth = config["depth"]
        self.randomness = config["randomness"]
        self.difficulty_name = config["name"]
    
    def evaluate_window(self, window: List[str], ai_symbol: str, player_symbol: str) -> int:
        """Verbesserte Fensterbewertung mit genaueren Heuristiken"""
        score = 0
        ai_count = window.count(ai_symbol)
        player_count = window.count(player_symbol)
        empty_count = window.count("⚪")
        
        # AI-Bewertung
        if ai_count == 4:
            score += 10000  # Gewinn
        elif ai_count == 3 and empty_count == 1:
            score += 100  # Fast gewonnen
        elif ai_count == 2 and empty_count == 2:
            score += 10  # Gute Position
        elif ai_count == 1 and empty_count == 3:
            score += 1  # Basis-Position
        
        # Gegner-Bewertung (Verteidigung)
        if player_count == 4:
            score -= 10000  # Verloren (sollte nicht passieren)
        elif player_count == 3 and empty_count == 1:
            score -= 500  # Muss blocken!
        elif player_count == 2 and empty_count == 2:
            score -= 50  # Gefährliche Position
        
        return score
    
    def score_position(self, board: List[List[str]], ai_symbol: str, player_symbol: str) -> int:
        """Verbesserte Positionsbewertung mit strategischen Präferenzen"""
        score = 0
        
        # Zentrum bevorzugen (stärkere Gewichtung)
        center_array = [board[i][COLUMNS // 2] for i in range(ROWS)]
        center_count = center_array.count(ai_symbol)
        score += center_count * 6
        
        # Mittlere Spalten bevorzugen
        for row in range(ROWS):
            for col in [2, 3, 4]:  # Mittlere Spalten
                if board[row][col] == ai_symbol:
                    score += 2
        
        # Horizontal scannen
        for row in range(ROWS):
            for col in range(COLUMNS - 3):
                window = board[row][col:col + 4]
                score += self.evaluate_window(window, ai_symbol, player_symbol)
        
        # Vertikal scannen
        for col in range(COLUMNS):
            for row in range(ROWS - 3):
                window = [board[row + i][col] for i in range(4)]
                score += self.evaluate_window(window, ai_symbol, player_symbol)
        
        # Diagonal (rechts-unten)
        for row in range(ROWS - 3):
            for col in range(COLUMNS - 3):
                window = [board[row + i][col + i] for i in range(4)]
                score += self.evaluate_window(window, ai_symbol, player_symbol)
        
        # Diagonal (rechts-oben)
        for row in range(3, ROWS):
            for col in range(COLUMNS - 3):
                window = [board[row - i][col + i] for i in range(4)]
                score += self.evaluate_window(window, ai_symbol, player_symbol)
        
        return score
    
    def get_valid_columns(self, board: List[List[str]]) -> List[int]:
        """Gibt alle gültigen Spalten zurück"""
        return [col for col in range(COLUMNS) if board[0][col] == "⚪"]
    
    def is_terminal_node(self, board: List[List[str]], ai_symbol: str, player_symbol: str) -> Tuple[bool, Optional[str]]:
        """Prüft ob das Spiel beendet ist und wer gewonnen hat"""
        # Check für Gewinn
        for symbol in [ai_symbol, player_symbol]:
            # Horizontal
            for row in range(ROWS):
                for col in range(COLUMNS - 3):
                    if all(board[row][col + i] == symbol for i in range(4)):
                        return True, symbol
            
            # Vertikal
            for col in range(COLUMNS):
                for row in range(ROWS - 3):
                    if all(board[row + i][col] == symbol for i in range(4)):
                        return True, symbol
            
            # Diagonal (rechts-unten)
            for row in range(ROWS - 3):
                for col in range(COLUMNS - 3):
                    if all(board[row + i][col + i] == symbol for i in range(4)):
                        return True, symbol
            
            # Diagonal (rechts-oben)
            for row in range(3, ROWS):
                for col in range(COLUMNS - 3):
                    if all(board[row - i][col + i] == symbol for i in range(4)):
                        return True, symbol
        
        # Check für Unentschieden
        if len(self.get_valid_columns(board)) == 0:
            return True, None
        
        return False, None
    
    def minimax(self, board: List[List[str]], depth: int, alpha: float, beta: float, 
                maximizing: bool, ai_symbol: str, player_symbol: str) -> Tuple[Optional[int], float]:
        """Optimierter Minimax mit Alpha-Beta-Pruning und Move-Ordering"""
        valid_cols = self.get_valid_columns(board)
        is_terminal, winner = self.is_terminal_node(board, ai_symbol, player_symbol)
        
        # Terminal-Zustände
        if depth == 0 or is_terminal:
            if is_terminal:
                if winner == ai_symbol:
                    return None, 100000000
                elif winner == player_symbol:
                    return None, -100000000
                else:
                    return None, 0
            else:
                return None, self.score_position(board, ai_symbol, player_symbol)
        
        # Move ordering: Zentrum zuerst prüfen
        valid_cols.sort(key=lambda x: abs(x - COLUMNS // 2))
        
        if maximizing:
            value = float('-inf')
            column = random.choice(valid_cols) if valid_cols else None
            
            for col in valid_cols:
                temp_board = [row[:] for row in board]
                self._drop_piece(temp_board, col, ai_symbol)
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, False, ai_symbol, player_symbol)[1]
                
                if new_score > value:
                    value = new_score
                    column = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Beta cutoff
            
            return column, value
        else:
            value = float('inf')
            column = random.choice(valid_cols) if valid_cols else None
            
            for col in valid_cols:
                temp_board = [row[:] for row in board]
                self._drop_piece(temp_board, col, player_symbol)
                new_score = self.minimax(temp_board, depth - 1, alpha, beta, True, ai_symbol, player_symbol)[1]
                
                if new_score < value:
                    value = new_score
                    column = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break  # Alpha cutoff
            
            return column, value
    
    def _drop_piece(self, board: List[List[str]], column: int, symbol: str) -> Optional[int]:
        """Lässt einen Spielstein in die Spalte fallen und gibt die Zeile zurück"""
        for row in reversed(range(ROWS)):
            if board[row][column] == "⚪":
                board[row][column] = symbol
                return row
        return None
    
    def get_best_move(self, board: List[List[str]], ai_symbol: str, player_symbol: str) -> int:
        """Gibt den besten Zug zurück mit optionaler Zufälligkeit"""
        valid_cols = self.get_valid_columns(board)
        
        if not valid_cols:
            return 0
        
        # Zufälligkeit für niedrigere Schwierigkeitsgrade
        if random.random() < self.randomness:
            return random.choice(valid_cols)
        
        # Prüfe auf sofortigen Gewinnzug
        for col in valid_cols:
            temp_board = [row[:] for row in board]
            self._drop_piece(temp_board, col, ai_symbol)
            is_terminal, winner = self.is_terminal_node(temp_board, ai_symbol, player_symbol)
            if is_terminal and winner == ai_symbol:
                return col
        
        # Prüfe ob Gegner blockiert werden muss
        for col in valid_cols:
            temp_board = [row[:] for row in board]
            self._drop_piece(temp_board, col, player_symbol)
            is_terminal, winner = self.is_terminal_node(temp_board, ai_symbol, player_symbol)
            if is_terminal and winner == player_symbol:
                return col
        
        # Verwende Minimax für den besten Zug
        column, _ = self.minimax(board, self.max_depth, float('-inf'), float('inf'), 
                                 True, ai_symbol, player_symbol)
        
        return column if column is not None else random.choice(valid_cols)

# ───────────────────────────────────────────────
# >> Game Timer
# ───────────────────────────────────────────────
class GameTimer:
    """Verwaltet Zugzeiten und Gesamtspielzeit"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.move_times: List[timedelta] = []
        self.current_move_start: Optional[datetime] = None
    
    def start_move(self):
        """Startet den Timer für einen Zug"""
        self.current_move_start = datetime.now()
    
    def end_move(self):
        """Beendet den Timer für einen Zug"""
        if self.current_move_start:
            duration = datetime.now() - self.current_move_start
            self.move_times.append(duration)
            self.current_move_start = None
    
    def get_game_duration(self) -> timedelta:
        """Gibt die Gesamtspielzeit zurück"""
        return datetime.now() - self.start_time
    
    def get_average_move_time(self) -> Optional[timedelta]:
        """Gibt die durchschnittliche Zugzeit zurück"""
        if not self.move_times:
            return None
        return sum(self.move_times, timedelta()) / len(self.move_times)

# ───────────────────────────────────────────────
# >> Enhanced Button & View
# ───────────────────────────────────────────────
class Connect4Button(Button):
    def __init__(self, column, view):
        # Dynamische Farben basierend auf Spalte
        styles = [
            discord.ButtonStyle.primary,
            discord.ButtonStyle.secondary,
            discord.ButtonStyle.success,
        ]
        style = styles[column % 3]
        
        # Verteile Buttons auf 2 Reihen (4 + 3)
        row = 0 if column < 4 else 1
        
        super().__init__(style=style, label=str(column + 1), row=row)
        self.column = column
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        view = self.view_ref
        msgs = view.messages

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
                msgs["cog_4gewinnt"]["error_types"]["not_your_turn"],
                ephemeral=True
            )
            return
        
        # AI mode checks
        if view.is_ai_mode and interaction.user != view.player1:
            await interaction.response.send_message(
                msgs["cog_4gewinnt"]["error_types"]["not_your_turn"],
                ephemeral=True
            )
            return

        # End move timer
        view.timer.end_move()

        if not view.make_move(self.column):
            await interaction.response.send_message(
                msgs["cog_4gewinnt"]["error_types"]["this_column_full"],
                ephemeral=True
            )
            view.timer.start_move()
            return

        winner = view.check_winner()
        board_str = view.board_to_str()
        
        if winner or view.is_draw():
            await view.end_game(interaction, winner, board_str)
            return

        view.switch_player()
        
        # AI turn
        if view.is_ai_mode and view.current_player == view.player2:
            await interaction.response.edit_message(
                content=f"🤖 **{view.ai.difficulty_name} KI denkt nach...**\n{board_str}",
                view=view
            )
            
            # Simuliere Denkzeit (abhängig von Schwierigkeit)
            think_time = {
                "easy": 0.5,
                "medium": 1.0,
                "hard": 1.5
            }
            await asyncio.sleep(think_time.get(view.difficulty, 1.0))
            
            view.timer.start_move()
            ai_col = view.ai.get_best_move(view.board, view.current_symbol, "🔴")
            view.timer.end_move()
            
            view.make_move(ai_col)
            
            winner = view.check_winner()
            board_str = view.board_to_str()
            
            if winner or view.is_draw():
                await view.end_game(interaction, winner, board_str, is_followup=True)
                return
            
            view.switch_player()
            view.timer.start_move()
            
            # Automatisches Update nach KI-Zug
            await interaction.edit_original_response(
                content=f"✅ KI hat Spalte **{ai_col + 1}** gewählt!\n\n"
                        f"{view.current_player.mention}, du bist dran! 🔴\n\n"
                        f"{board_str}\n"
                        f"Zug: {view.move_count}",
                view=view
            )
        else:
            view.timer.start_move()
            await interaction.response.edit_message(
                content=msgs["cog_4gewinnt"]["message"]["player_turn"].format(
                    current_player=view.current_player.mention,
                    board_str=board_str,
                    move_count=view.move_count
                ),
                view=view
            )

class Connect4View(View):
    def __init__(self, player1, player2, messages, is_ai_mode=False, difficulty="medium"):
        super().__init__(timeout=DEFAULT_TIMEOUT)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_symbol = "🔴"
        self.board = [["⚪" for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.messages = messages
        self.is_ai_mode = is_ai_mode
        self.difficulty = difficulty
        self.ai = Connect4AI(difficulty) if is_ai_mode else None
        self.timer = GameTimer()
        self.move_count = 0
        self.move_history: List[tuple] = []
        self.game_ended = False

        for col in range(COLUMNS):
            self.add_item(Connect4Button(col, self))
        
        # Start timer for first move
        self.timer.start_move()

    def make_move(self, column: int) -> bool:
        """Führt einen Zug aus"""
        if column < 0 or column >= COLUMNS:
            return False
            
        for row in reversed(range(ROWS)):
            if self.board[row][column] == "⚪":
                self.board[row][column] = self.current_symbol
                self.move_history.append((row, column, self.current_symbol))
                self.move_count += 1
                return True
        return False

    def switch_player(self):
        """Wechselt den aktuellen Spieler"""
        if self.current_player == self.player1:
            self.current_player = self.player2
            self.current_symbol = "🟡"
        else:
            self.current_player = self.player1
            self.current_symbol = "🔴"

    def check_winner(self) -> bool:
        """Überprüft, ob es einen Gewinner gibt"""
        b = self.board
        
        # horizontal
        for row in range(ROWS):
            for col in range(COLUMNS - 3):
                if (b[row][col] == b[row][col+1] == b[row][col+2] == b[row][col+3] 
                    and b[row][col] != "⚪"):
                    return True
        
        # vertikal
        for col in range(COLUMNS):
            for row in range(ROWS - 3):
                if (b[row][col] == b[row+1][col] == b[row+2][col] == b[row+3][col] 
                    and b[row][col] != "⚪"):
                    return True
        
        # diagonal rechts unten
        for row in range(ROWS - 3):
            for col in range(COLUMNS - 3):
                if (b[row][col] == b[row+1][col+1] == b[row+2][col+2] == b[row+3][col+3] 
                    and b[row][col] != "⚪"):
                    return True
        
        # diagonal rechts oben
        for row in range(3, ROWS):
            for col in range(COLUMNS - 3):
                if (b[row][col] == b[row-1][col+1] == b[row-2][col+2] == b[row-3][col+3] 
                    and b[row][col] != "⚪"):
                    return True
        
        return False

    def is_draw(self) -> bool:
        """Überprüft, ob das Spiel unentschieden ist"""
        return all(cell != "⚪" for row in self.board for cell in row)

    def board_to_str(self) -> str:
        """Konvertiert das Board zu einem String"""
        numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
        header = "".join(numbers)
        board_rows = "\n".join("".join(row) for row in self.board)
        return f"{header}\n{board_rows}"
    
    async def end_game(self, interaction: discord.Interaction, winner: bool, board_str: str, is_followup: bool = False):
        """Beendet das Spiel und zeigt Statistiken"""
        self.game_ended = True
        
        for child in self.children:
            child.disabled = True
        
        msgs = self.messages
        game_duration = self.timer.get_game_duration()
        avg_move_time = self.timer.get_average_move_time()
        
        # Update statistics
        if winner:
            if self.is_ai_mode:
                if self.current_player == self.player1:
                    game_stats.record_win(self.player1.id, vs_ai=True)
                else:
                    game_stats.record_loss(self.player1.id, vs_ai=True)
            else:
                game_stats.record_win(self.current_player.id)
                other_player = self.player2 if self.current_player == self.player1 else self.player1
                game_stats.record_loss(other_player.id)
        else:
            game_stats.record_draw(self.player1.id)
            if not self.is_ai_mode:
                game_stats.record_draw(self.player2.id)
        
        # Build result message
        embed = discord.Embed(
            title="🎮 4 Gewinnt - Spiel beendet!",
            color=discord.Color.gold() if winner else discord.Color.greyple()
        )
        
        # Ergebnis
        if winner:
            if self.is_ai_mode and self.current_player == self.player2:
                result_text = f"🤖 **Die {self.ai.difficulty_name} KI hat gewonnen!**"
                embed.color = discord.Color.red()
            else:
                result_text = msgs["cog_4gewinnt"]["win_types"]["win"].format(
                    winner=self.current_player.mention
                )
                embed.color = discord.Color.green()
        else:
            result_text = msgs["cog_4gewinnt"]["win_types"]["draw"]
        
        embed.add_field(
            name="🎯 Ergebnis",
            value=result_text,
            inline=False
        )
        
        # Spielstatistiken
        avg_time_str = f"{avg_move_time.seconds}s" if avg_move_time else "0s"
        embed.add_field(
            name="📊 Spielstatistiken",
            value=f"⏱️ Spielzeit: {game_duration.seconds // 60}m {game_duration.seconds % 60}s\n"
                  f"🔢 Züge: {self.move_count}\n"
                  f"⚡ Ø Zugzeit: {avg_time_str}",
            inline=True
        )
        
        # Sieger-Stats
        if winner:
            winner_stats = game_stats.get_user_stats(self.current_player.id if not self.is_ai_mode or self.current_player == self.player1 else self.player1.id)
            
            if self.is_ai_mode:
                if self.current_player == self.player1:
                    stats_text = f"🏆 Siege vs KI: {winner_stats['ai_wins']}\n💔 Niederlagen vs KI: {winner_stats['ai_losses']}\n🔥 Aktuelle Serie: {winner_stats['win_streak']}"
                else:
                    stats_text = f"Die KI bleibt ungeschlagen! 🤖"
            else:
                stats_text = f"🏆 Siege: {winner_stats['wins']}\n💔 Niederlagen: {winner_stats['losses']}\n🔥 Serie: {winner_stats['win_streak']}"
            
            embed.add_field(
                name="📈 Spieler-Stats",
                value=stats_text,
                inline=True
            )
        
        # Spielfeld
        embed.add_field(
            name="🎲 Endposition",
            value=f"```\n{board_str}\n```",
            inline=False
        )
        
        embed.set_footer(text=f"Spiel-ID: {interaction.id} • Schwierigkeit: {self.ai.difficulty_name if self.is_ai_mode else 'PvP'}")
        embed.timestamp = datetime.now()
        
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
class Connect4Cog(ezcord.Cog, group="fun"):
    
    @commands.slash_command(name="connect4", description="Starte ein 4 Gewinnt Spiel!")
    async def connect4(
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
            lang_code = self.bot.get_user_language(ctx.author.id)
        except AttributeError:
            lang_code = "de"
        
        try:
            messages = load_messages(lang_code)
        except FileNotFoundError as e:
            print(f"CRITICAL: {e}")
            messages = {"cog_4gewinnt": {"error_types": {}, "message": {}, "win_types": {}}}

        # AI mode
        if opponent is None:
            ai_user = ctx.guild.me
            view = Connect4View(ctx.author, ai_user, messages, is_ai_mode=True, difficulty=difficulty)
            
            difficulty_info = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])
            difficulty_emoji = {"easy": "😊", "medium": "🤔", "hard": "😈"}
            
            await ctx.respond(
                f"🤖 **4 Gewinnt vs KI** {difficulty_emoji.get(difficulty, '🤖')}\n"
                f"**Schwierigkeit:** {difficulty_info['name']}\n"
                f"{ctx.author.mention} 🔴 spielt gegen die KI! 🟡\n\n"
                f"{view.board_to_str()}",
                view=view
            )
            return

        # PvP mode validations
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
        
        await ctx.respond(
            f"🎮 **4 Gewinnt - PvP Match**\n"
            f"{ctx.author.mention} 🔴 vs 🟡 {opponent.mention}\n\n"
            f"{view.board_to_str()}",
            view=view
        )
    
    @commands.slash_command(name="connect4stats", description="Zeige deine 4 Gewinnt Statistiken!")
    async def stats(self, ctx: discord.ApplicationContext, user: Optional[discord.Member] = None):
        target_user = user or ctx.author
        stats = game_stats.get_user_stats(target_user.id)
        winrate = game_stats.get_winrate(target_user.id)
        
        embed = discord.Embed(
            title=f"📊 4 Gewinnt Statistiken - {target_user.display_name}",
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
        embed.timestamp = datetime.now()
        
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Connect4Cog(bot))
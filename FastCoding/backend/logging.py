import colorama
from colorama import Fore, Style
from datetime import datetime
colorama.init(autoreset=True)

time = datetime.now().strftime(f"[{Fore.CYAN}%H:%M{Style.RESET_ALL}]")

def init_spam_db():
    print(f"{time} [{Style.BRIGHT}{Fore.MAGENTA}DATABASE{Style.RESET_ALL}] Spam database initialized successfully.")

def init_warn_db():
    print(f"{time} [{Style.BRIGHT}{Fore.MAGENTA}DATABASE{Style.RESET_ALL}] Warn database initialized successfully.")

def init_notes_db():
    print(f"{time} [{Style.BRIGHT}{Fore.MAGENTA}DATABASE{Style.RESET_ALL}] Notes database initialized successfully.")

def init_tempvc_db():
    print(f"{time} [{Style.BRIGHT}{Fore.MAGENTA}DATABASE{Style.RESET_ALL}] TempVC database initialized successfully.")

def init_all():
    init_spam_db()
    init_notes_db()
    init_warn_db()
    init_tempvc_db()
# src/managerx/cli.py
import click
import os

FOLDER_STRUCTURE = [
    "src/handler",
    "src/DevTools/backend/utils",
    "src/DevTools/backend/database",
    "src/DevTools/backend/config",
    "src/cogs/fun/wikipedia",
    "src/cogs/information",
    "src/cogs/moderation",
    "src/cogs/servermanagement",
    "src/managerx",
]

@click.group()
def managerx():
    """ManagerX CLI Tool"""
    pass

@managerx.command()
def create():
    """Erstellt automatisch die komplette ManagerX-Ordnerstruktur"""
    root_folder = "ManagerX"
    root_path = os.path.join(os.getcwd(), root_folder)

    if os.path.exists(root_path):
        click.echo(f"Ordner '{root_folder}' existiert bereits. Bitte löschen oder umbenennen!")
        return

    for path in FOLDER_STRUCTURE:
        full_path = os.path.join(root_path, path)
        os.makedirs(full_path, exist_ok=True)

        # Automatisch __init__.py erstellen, damit Python-Pakete erkannt werden
        if path.endswith("managerx") or "DevTools" in path or "cogs" in path:
            init_file = os.path.join(full_path, "__init__.py")
            with open(init_file, "w") as f:
                f.write("# Init for package\n")

    click.echo(f"ManagerX-Ordnerstruktur wurde erfolgreich in '{root_folder}' erstellt!")

if __name__ == "__main__":
    managerx()

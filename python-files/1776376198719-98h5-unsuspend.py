import requests
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.text import Text
from rich.progress_bar import ProgressBar

console = Console()

KANJI_DECK = "Recognition RTK 630"
SENTENCES_DECK = "Sentence"
SENTENCES_WORD_FIELD = "Word"
KANJI_FIELD = "Kanji"


def invoke(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post("http://localhost:8765", json=payload).json()
        if response.get("error"):
            raise Exception(response["error"])
        return response["result"]
    except Exception:
        console.print("[bold red]Error: Anki is not running.[/bold red]")
        exit(1)


def get_cards_info_batch(card_ids, progress, task_id, batch_size=500):
    all_info = []
    for i in range(0, len(card_ids), batch_size):
        batch = card_ids[i : i + batch_size]
        info = invoke("cardsInfo", cards=batch)
        all_info.extend(info)
        progress.update(task_id, advance=len(batch))
    return all_info


def main():
    console.print("\n")
    console.print(
        Panel.fit(f"[bold white]Sync: {KANJI_DECK}[/bold white]", style="blue")
    )

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}", justify="left"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        console=console,
    )

    try:
        with progress:
            t1 = progress.add_task("[cyan]Analyzing Sentences ", total=None)
            s_ids = invoke("findCards", query=f"deck:{SENTENCES_DECK}")
            progress.update(t1, total=len(s_ids))
            s_info = get_cards_info_batch(s_ids, progress, t1)

            unique_chars = {
                char
                for c in s_info
                for char in "".join(c["fields"][SENTENCES_WORD_FIELD]["value"].split())
            }

            t2 = progress.add_task("[yellow]Checking Kanji     ", total=None)
            all_kanji_ids = invoke("findCards", query=f'deck:"{KANJI_DECK}"')
            suspended_ids = invoke(
                "findCards", query=f'deck:"{KANJI_DECK}" is:suspended'
            )

            total_kanji = len(all_kanji_ids)
            initially_suspended = len(suspended_ids)
            initially_active = total_kanji - initially_suspended

            progress.update(t2, total=initially_suspended)
            suspended_info = get_cards_info_batch(suspended_ids, progress, t2)

            to_open_ids = []
            new_chars = []
            for card in suspended_info:
                char = card["fields"].get(KANJI_FIELD, {}).get("value", "").strip()
                if char in unique_chars:
                    to_open_ids.append(card["cardId"])
                    new_chars.append(char)

            if to_open_ids:
                invoke("unsuspend", cards=to_open_ids)

        unlocked_now = len(to_open_ids)
        final_active = initially_active + unlocked_now
        percent = (final_active / total_kanji) * 100 if total_kanji > 0 else 0

        stats_table = Table(show_header=False, box=None, padding=(0, 1))
        stats_table.add_row("Total kanji in deck:", f"[white]{total_kanji}[/white]")
        stats_table.add_row("Previously active:", f"[blue]{initially_active}[/blue]")
        stats_table.add_row(
            "Unlocked now:", f"[bold green]+{unlocked_now}[/bold green]"
        )
        stats_table.add_row(
            "Total active:", f"[bold magenta]{final_active}[/bold magenta]"
        )

        pbar = ProgressBar(total=total_kanji, completed=final_active, width=50)

        summary_group = Group(
            stats_table,
            Text(f"\n Deck progress: {percent:.1f}%\n", style="bold white"),
            pbar,
        )

        console.print(
            Panel(
                summary_group,
                title="Summary",
                border_style="bright_blue",
                padding=(1, 2),
                expand=False,
            )
        )

        if new_chars:
            kanji_cloud = Text()
            for i, char in enumerate(new_chars):
                kanji_cloud.append(char, style="bold green")
                if i < len(new_chars) - 1:
                    kanji_cloud.append("  ")

            console.print(
                Panel(
                    kanji_cloud,
                    title="Unlocked this time",
                    border_style="green",
                    expand=False,
                    padding=(1, 2),
                )
            )
        else:
            console.print("[dim italic]No new matches found.[/dim italic]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()

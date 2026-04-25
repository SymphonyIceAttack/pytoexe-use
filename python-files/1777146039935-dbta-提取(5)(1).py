
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import aiohttp
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.table import Table


API_URL = "https://api.hotmail666.com/api/extract-mail"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)
REQUEST_QUANTITY = 1
MAX_WORKERS = 100


class MailType(Enum):
    BACKUP_OUTLOOK = "backup_outlook"
    BACKUP_HOTMAIL = "backup_hotmail"
    HOTMAIL = "hotmail"
    OUTLOOK = "outlook"


@dataclass(slots=True)
class ExtractResult:
    success: bool
    message: str
    request_id: str = ""
    mails: list[str] = field(default_factory=list)
    remaining_times: int | None = None


@dataclass(slots=True)
class RuntimeStats:
    total_requests: int = 0
    success_count: int = 0
    stock_empty_count: int = 0
    error_count: int = 0
    total_mails: int = 0
    remaining_times: int | None = None


CONSOLE = Console()
STATS = RuntimeStats()
STATS_LOCK = asyncio.Lock()
STOP_EVENT = asyncio.Event()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=CONSOLE, rich_tracebacks=True)],
    )


def build_headers() -> dict[str, str]:
    return {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DNT": "1",
        "Origin": "https://api.hotmail666.com",
        "Pragma": "no-cache",
        "Referer": "https://api.hotmail666.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36"
        ),
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


def choose_mail_type() -> MailType:
    options = list(MailType)
    table = Table(title="mailType 选择")
    table.add_column("序号", justify="center")
    table.add_column("mailType", style="cyan")

    for index, option in enumerate(options, start=1):
        table.add_row(str(index), option.value)

    CONSOLE.print(table)

    while True:
        selected = input("请输入 mailType 序号：").strip()
        if selected.isdigit():
            selected_index = int(selected)
            if 1 <= selected_index <= len(options):
                return options[selected_index - 1]
        CONSOLE.print("[red]输入无效，请重新输入正确的序号。[/red]")


def prompt_card_key() -> str:
    while True:
        card_key = input("请输入 cardKey（必填）：").strip()
        if card_key:
            return card_key
        CONSOLE.print("[red]cardKey 不能为空，请重新输入。[/red]")


def prompt_worker_count() -> int:
    while True:
        worker_text = input(f"请输入线程数（1-{MAX_WORKERS}）：").strip()
        if worker_text.isdigit():
            worker_count = int(worker_text)
            if 1 <= worker_count <= MAX_WORKERS:
                return worker_count
        CONSOLE.print(f"[red]线程数无效，请输入 1 到 {MAX_WORKERS} 之间的整数。[/red]")


def parse_response(payload: dict[str, Any]) -> ExtractResult:
    data = payload.get("data") or {}
    mails = data.get("mails") or []

    return ExtractResult(
        success=bool(payload.get("success")),
        message=str(payload.get("message", "")),
        request_id=str(data.get("requestId") or payload.get("data", {}).get("requestId", "")),
        mails=[str(mail) for mail in mails],
        remaining_times=data.get("remainingTimes"),
    )


async def extract_mail(
    session: aiohttp.ClientSession,
    card_key: str,
    mail_type: MailType,
) -> ExtractResult:
    payload = {
        "cardKey": card_key,
        "mailType": mail_type.value,
        "quantity": REQUEST_QUANTITY,
    }

    async with session.post(
        API_URL,
        headers=build_headers(),
        json=payload,
    ) as response:
        response.raise_for_status()
        result = parse_response(await response.json())
        return result


async def run_task(
    task_index: int,
    session: aiohttp.ClientSession,
    card_key: str,
    mail_type: MailType,
) -> None:
    while not STOP_EVENT.is_set():
        try:
            result = await extract_mail(session=session, card_key=card_key, mail_type=mail_type)
            if result.success:
                logging.info("协程 %s 提取成功，获取 %s 个邮箱。", task_index, len(result.mails))
                async with STATS_LOCK:
                    STATS.total_requests += 1
                    STATS.success_count += 1
                    STATS.total_mails += len(result.mails)
                    if result.remaining_times is not None:
                        STATS.remaining_times = result.remaining_times
                if result.mails:
                    with open("mails.txt", "a", encoding="utf-8") as f:
                        f.write("\n".join(result.mails) + "\n")
            elif result.message == "当前库存不足，请稍后重试":
                logging.warning("协程 %s 库存不足。", task_index)
                async with STATS_LOCK:
                    STATS.total_requests += 1
                    STATS.stock_empty_count += 1
            else:
                logging.warning("协程 %s 提取失败：%s", task_index, result.message)
                async with STATS_LOCK:
                    STATS.total_requests += 1
                    STATS.error_count += 1
                if result.message in ("卡密无效或已过期", ) or "剩余次数不足" in result.message:
                    logging.error("触发终止条件（%s），停止所有协程。", result.message)
                    STOP_EVENT.set()
                    break
        except aiohttp.ClientError as exc:
            logging.error("协程 %s 请求异常：%s", task_index, exc)
            async with STATS_LOCK:
                STATS.total_requests += 1
                STATS.error_count += 1
        except asyncio.TimeoutError as exc:
            logging.error("协程 %s 请求超时：%s", task_index, exc)
            async with STATS_LOCK:
                STATS.total_requests += 1
                STATS.error_count += 1
        except ValueError as exc:
            logging.error("协程 %s 响应解析失败：%s", task_index, exc)
            async with STATS_LOCK:
                STATS.total_requests += 1
                STATS.error_count += 1


def build_stats_table(mail_type: MailType, worker_count: int) -> Table:
    stats_table = Table(title="实时统计面板")
    stats_table.add_column("项目", style="cyan")
    stats_table.add_column("值", style="green")
    stats_table.add_row("mailType", mail_type.value)
    stats_table.add_row("并发数", str(worker_count))
    stats_table.add_row("总请求数", str(STATS.total_requests))
    stats_table.add_row("成功数", str(STATS.success_count))
    stats_table.add_row("库存不足数", str(STATS.stock_empty_count))
    stats_table.add_row("异常数", str(STATS.error_count))
    stats_table.add_row("累计提取邮箱数", str(STATS.total_mails))
    stats_table.add_row(
        "剩余次数",
        "-" if STATS.remaining_times is None else str(STATS.remaining_times),
    )
    return stats_table


async def render_stats_panel(mail_type: MailType, worker_count: int) -> None:
    with Live(build_stats_table(mail_type, worker_count), console=CONSOLE, refresh_per_second=4) as live:
        while True:
            async with STATS_LOCK:
                live.update(build_stats_table(mail_type, worker_count))
            await asyncio.sleep(0.25)


async def main() -> None:
    setup_logging()
    card_key = prompt_card_key()
    mail_type = choose_mail_type()
    worker_count = prompt_worker_count()

    assert worker_count >= 1, "线程数必须大于等于 1"

    logging.info("开始异步并发提取，mailType=%s，并发数=%s", mail_type.value, worker_count)

    connector = aiohttp.TCPConnector(limit=worker_count)
    async with aiohttp.ClientSession(
        timeout=REQUEST_TIMEOUT,
        connector=connector,
    ) as session:
        panel_task = asyncio.create_task(render_stats_panel(mail_type, worker_count))
        tasks = [
            asyncio.create_task(run_task(task_index, session, card_key, mail_type))
            for task_index in range(1, worker_count + 1)
        ]
        try:
            await asyncio.gather(*tasks)
        finally:
            panel_task.cancel()
            await asyncio.gather(panel_task, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        CONSOLE.print("\n[yellow]已手动停止运行。[/yellow]")

#!/usr/bin/env python3
"""
Скрипт проверяет доступность списка адресов host:port.
Так как это host:port (а не просто IP), классический ICMP ping здесь
не подходит — вместо него делается TCP-подключение (socket.connect),
что фактически проверяет доступность именно нужного порта/сервиса.

Для каждого адреса делается 4 попытки, для каждой выводится результат
(успех/неудача + время отклика в мс), а в конце — сводная таблица.
"""

import socket
import time
import statistics

# Список адресов для проверки в формате "host:port"
ADDRESSES = [
    "cdn01.crpt.ru:19101",
    "cdn02.crpt.ru:19101",
    "cdn03.crpt.ru:19101",
    "cdn04.crpt.ru:19101",
    "cdn05.crpt.ru:19101",
    "cdn06.crpt.ru:19101",
    "cdn07.crpt.ru:19101",
    "cdn08.crpt.ru:19101",
    "cdn09.crpt.ru:19101",
    "cdn10.crpt.ru:19101",
    "cdn11.crpt.ru:19101",
]

ATTEMPTS = 4          # количество попыток на каждый адрес
TIMEOUT = 3            # таймаут одной попытки, сек


def tcp_check(host: str, port: int, timeout: float = TIMEOUT):
    """
    Пытается установить TCP-соединение с host:port.
    Возвращает (успех: bool, время_отклика_мс: float или None, ошибка: str или None)
    """
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed_ms = (time.perf_counter() - start) * 1000
            return True, elapsed_ms, None
    except socket.timeout:
        return False, None, "таймаут"
    except socket.gaierror as e:
        return False, None, f"ошибка DNS ({e})"
    except OSError as e:
        return False, None, f"ошибка подключения ({e})"


def check_address(address: str):
    host, port_str = address.rsplit(":", 1)
    port = int(port_str)

    print(f"\n=== {address} ===")

    results = []
    for attempt in range(1, ATTEMPTS + 1):
        success, elapsed_ms, error = tcp_check(host, port)
        if success:
            print(f"  Попытка {attempt}: OK, время отклика {elapsed_ms:.1f} мс")
        else:
            print(f"  Попытка {attempt}: FAIL ({error})")
        results.append((success, elapsed_ms))

    successes = [r for r in results if r[0]]
    times = [r[1] for r in successes]

    loss = 100 * (ATTEMPTS - len(successes)) / ATTEMPTS
    summary = {
        "address": address,
        "sent": ATTEMPTS,
        "received": len(successes),
        "loss_percent": loss,
        "min_ms": min(times) if times else None,
        "avg_ms": statistics.mean(times) if times else None,
        "max_ms": max(times) if times else None,
    }

    if times:
        print(
            f"  Итог: {len(successes)}/{ATTEMPTS} успешно, "
            f"потери {loss:.0f}%, "
            f"min/avg/max = {summary['min_ms']:.1f}/{summary['avg_ms']:.1f}/{summary['max_ms']:.1f} мс"
        )
    else:
        print(f"  Итог: {len(successes)}/{ATTEMPTS} успешно, потери {loss:.0f}% (нет ни одного успешного ответа)")

    return summary


def main():
    print(f"Проверка {len(ADDRESSES)} адресов, по {ATTEMPTS} попытки на каждый (TCP-подключение, таймаут {TIMEOUT} с)")

    all_summaries = []
    for address in ADDRESSES:
        summary = check_address(address)
        all_summaries.append(summary)

    # Итоговая сводная таблица
    print("\n" + "=" * 70)
    print("СВОДНАЯ ТАБЛИЦА")
    print("=" * 70)
    header = f"{'Адрес':<25}{'Успешно':<10}{'Потери':<10}{'Avg, мс':<10}"
    print(header)
    print("-" * 70)
    for s in all_summaries:
        avg_str = f"{s['avg_ms']:.1f}" if s["avg_ms"] is not None else "-"
        print(
            f"{s['address']:<25}"
            f"{s['received']}/{s['sent']:<8}"
            f"{s['loss_percent']:.0f}%{'':<7}"
            f"{avg_str:<10}"
        )

    print("-" * 70)

    # Общее среднее время отклика по всем успешным попыткам всех адресов
    all_avg_values = [s["avg_ms"] for s in all_summaries if s["avg_ms"] is not None]
    if all_avg_values:
        overall_avg = statistics.mean(all_avg_values)
        print(f"{'Среднее по всем адресам':<45}{overall_avg:.1f} мс")
    else:
        print("Среднее по всем адресам: нет успешных ответов ни от одного адреса")

    unreachable = [s["address"] for s in all_summaries if s["received"] == 0]
    if unreachable:
        print(f"\nНедоступны полностью: {', '.join(unreachable)}")
    else:
        print("\nВсе адреса ответили хотя бы на одну попытку.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
برنامه پاک کردن فولدرهای مشترک
- فولدر مرکز (مرجع) را انتخاب می‌کند
- فولدر هدف را انتخاب می‌کند
- فولدرهایی که اسمشان در هر دو یکی است را پیدا می‌کند
- کل آن فولدرها را از فولدر هدف پاک می‌کند (با تأیید)
"""

import os
import sys
import shutil
from pathlib import Path


def get_folder_path(prompt: str) -> Path:
    """مسیر فولدر را از کاربر می‌گیرد و اعتبارسنجی می‌کند"""
    while True:
        path_str = input(prompt).strip().strip('"').strip("'")
        if not path_str:
            print("  ❌ مسیر خالی است. دوباره وارد کنید.")
            continue
        path = Path(path_str)
        if not path.exists():
            print(f"  ❌ مسیر وجود ندارد: {path}")
            continue
        if not path.is_dir():
            print(f"  ❌ این مسیر یک فولدر نیست: {path}")
            continue
        return path.resolve()


def get_subfolders(folder: Path) -> set[str]:
    """لیست نام فولدرهای سطح اول را برمی‌گرداند"""
    try:
        return {item.name for item in folder.iterdir() if item.is_dir()}
    except PermissionError:
        print(f"  ❌ دسترسی به فولدر ممکن نیست: {folder}")
        sys.exit(1)


def main():
    print("=" * 55)
    print("  برنامه پاک کردن فولدرهای مشترک")
    print("=" * 55)
    print()
    print("این برنامه فولدرهایی که اسمشان در هر دو فولدر یکی است")
    print("را پیدا می‌کند و از فولدر هدف پاک می‌کند.")
    print()

    # دریافت فولدر مرکز
    center = get_folder_path("📁 مسیر فولدر مرکز (مرجع) را وارد کنید: ")
    print(f"  ✓ فولدر مرکز: {center}")
    print()

    # دریافت فولدر هدف
    target = get_folder_path("📁 مسیر فولدر هدف را وارد کنید: ")
    print(f"  ✓ فولدر هدف: {target}")
    print()

    if center == target:
        print("❌ فولدر مرکز و هدف نمی‌توانند یکی باشند!")
        input("\nEnter را بزنید تا خارج شوید...")
        sys.exit(1)

    # پیدا کردن فولدرهای مشترک
    print("در حال بررسی فولدرها...")
    center_subs = get_subfolders(center)
    target_subs = get_subfolders(target)

    common = sorted(center_subs & target_subs)

    if not common:
        print()
        print("✅ هیچ فولدر مشترکی پیدا نشد. چیزی پاک نمی‌شود.")
        input("\nEnter را بزنید تا خارج شوید...")
        return

    print()
    print(f"🔍 {len(common)} فولدر مشترک پیدا شد:")
    print("-" * 40)
    for i, name in enumerate(common, 1):
        print(f"  {i}. {name}")
    print("-" * 40)
    print()
    print("⚠️  این فولدرها به طور کامل از فولدر هدف پاک خواهند شد!")
    print()

    confirm = input("آیا مطمئن هستید؟ (بله / خیر): ").strip().lower()
    if confirm not in ("بله", "ب", "yes", "y"):
        print()
        print("❌ عملیات لغو شد. هیچ چیزی پاک نشد.")
        input("\nEnter را بزنید تا خارج شوید...")
        return

    print()
    print("در حال پاک کردن...")
    deleted = 0
    failed = 0

    for name in common:
        folder_to_delete = target / name
        try:
            shutil.rmtree(folder_to_delete)
            print(f"  ✓ پاک شد: {name}")
            deleted += 1
        except Exception as e:
            print(f"  ❌ خطا در پاک کردن {name}: {e}")
            failed += 1

    print()
    print("=" * 40)
    print(f"✅ تعداد پاک‌شده: {deleted}")
    if failed:
        print(f"❌ تعداد ناموفق: {failed}")
    print("=" * 40)
    input("\nEnter را بزنید تا خارج شوید...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ عملیات توسط کاربر متوقف شد.")
        sys.exit(0)

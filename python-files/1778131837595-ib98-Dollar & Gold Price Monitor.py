#!/usr/bin/env python
# coding: utf-8

import requests
from bs4 import BeautifulSoup
import sys
import warnings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

warnings.filterwarnings('ignore')

# استفاده از Rich Console برای نمایش زیبا
console = Console()

def get_prices():
    try:
        # Get Dollar price
        dollar_url = "https://www.tgju.org/profile/price_dollar_rl"
        dollar_response = requests.get(dollar_url, timeout=10)
        
        # Get Gold price
        gold_url = "https://www.tgju.org/profile/geram18"
        gold_response = requests.get(gold_url, timeout=10)
        
        if dollar_response.status_code == 200 and gold_response.status_code == 200:
            dollar_soup = BeautifulSoup(dollar_response.text, 'html.parser')
            gold_soup = BeautifulSoup(gold_response.text, 'html.parser')
            
            # Extract Dollar prices
            dollar_current_label = dollar_soup.find(string="نرخ فعلی")
            dollar_highest_label = dollar_soup.find(string="بالاترین قیمت روز")
            dollar_lowest_label = dollar_soup.find(string="پایین ترین قیمت روز")
            
            # Extract Gold prices
            gold_current_label = gold_soup.find(string="نرخ فعلی")
            gold_highest_label = gold_soup.find(string="بالاترین قیمت روز")
            gold_lowest_label = gold_soup.find(string="پایین ترین قیمت روز")
            
            if (dollar_current_label and dollar_highest_label and dollar_lowest_label and
                gold_current_label and gold_highest_label and gold_lowest_label):
                
                # Dollar prices (in Tomans)
                dollar_current = dollar_current_label.find_next().text.strip()
                dollar_highest = dollar_highest_label.find_next().text.strip()
                dollar_lowest = dollar_lowest_label.find_next().text.strip()
                
                # Gold prices (convert Rials to Tomans)
                gold_current_raw = gold_current_label.find_next().text.strip()
                gold_highest_raw = gold_highest_label.find_next().text.strip()
                gold_lowest_raw = gold_lowest_label.find_next().text.strip()
                
                gold_current = int(gold_current_raw.replace(',', '')) / 10
                gold_highest = int(gold_highest_raw.replace(',', '')) / 10
                gold_lowest = int(gold_lowest_raw.replace(',', '')) / 10
                
                # --- بخش زیباسازی شده با Rich (همان داده‌ها، نمایش حرفه‌ای‌تر) ---
                
                # ساخت هدر زیبا
                header_text = Text("Amir Soleymanpour - Dollar & Gold Price Monitor", style="bold white on blue")
                header_panel = Panel(header_text, border_style="bright_blue", padding=(1, 2))
                console.print(header_panel)
                
                # ساخت جدول اصلی
                table = Table(title="📊 Live Market Data", title_style="bold cyan", border_style="blue")
                table.add_column("Field", style="cyan", no_wrap=True, width=20)
                table.add_column("US Dollar", justify="center", style="yellow", width=25)
                table.add_column("18K Gold", justify="center", style="yellow", width=25)
                
                # اضافه کردن ردیف‌ها با همان داده‌ها
                table.add_row("💵 Current Rate", f"{dollar_current} Tomans", f"{gold_current:>10,.0f} Tomans")
                table.add_row("📈 Highest Daily", f"{dollar_highest} Tomans", f"{gold_highest:>10,.0f} Tomans")
                table.add_row("📉 Lowest Daily", f"{dollar_lowest} Tomans", f"{gold_lowest:>10,.0f} Tomans")
                
                console.print(table)
                
                # فوتر با توضیحات
                note_text = Text("Note: Gold prices converted from Rials to Tomans (÷10)", style="italic dim")
                footer_panel = Panel(note_text, border_style="bright_blue", padding=(1, 1))
                console.print(footer_panel)
                
                # خط جداکننده نهایی
                console.print("=" * 70, style="dim")
                console.print()
                
            else:
                console.print("[red]Error: Page structure has changed[/red]")
        else:
            console.print(f"[red]Error receiving data (Dollar: {dollar_response.status_code}, Gold: {gold_response.status_code})[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("[red]Error: No internet connection[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    get_prices()
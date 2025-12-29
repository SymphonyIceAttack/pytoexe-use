import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import pandas as pd
import threading
import csv

# --- LOGIC ---

def run_search_logic(api_key, domains_str, titles_str, log_widget):
    """
    The background logic that actually fetches the data.
    """
    API_URL = "https://api.apollo.io/v1/mixed_people/search"
    
    # Process inputs
    domains = [d.strip() for d in domains_str.split(',') if d.strip()]
    titles = [t.strip() for t in titles_str.split(',') if t.strip()]
    
    if not domains or not titles:
        log_widget.insert(tk.END, "❌ Error: Please enter at least one domain and one job title.\n")
        return

    log_widget.insert(tk.END, f"🚀 Starting search for {len(domains)} companies...\n")
    
    all_leads = []
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }

    for domain in domains:
        log_widget.insert(tk.END, f"   🔎 Scanning: {domain}...\n")
        log_widget.see(tk.END) # Auto-scroll
        
        data = {
            "q_organization_domains": domain,
            "person_titles": titles,
            "page": 1,
            "per_page": 10
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()
            people = response.json().get('people', [])
            
            count = 0
            for lead in people:
                if lead.get('email'):
                    lead_info = {
                        "First Name": lead.get('first_name'),
                        "Last Name": lead.get('last_name'),
                        "Title": lead.get('title'),
                        "Email": lead.get('email'),
                        "Company": lead.get('organization', {}).get('name'),
                        "Domain": domain
                    }
                    all_leads.append(lead_info)
                    count += 1
            
            log_widget.insert(tk.END, f"      ✅ Found {count} leads with emails.\n")

        except Exception as e:
            log_widget.insert(tk.END, f"      ❌ Error: {str(e)}\n")

    # Save to CSV
    if all_leads:
        filename = "leads_export.csv"
        try:
            df = pd.DataFrame(all_leads)
            df.to_csv(filename, index=False)
            log_widget.insert(tk.END, f"\n🎉 DONE! Saved {len(all_leads)} leads to '{filename}'.\n")
            messagebox.showinfo("Success", f"Search complete! Saved {len(all_leads)} leads to {filename}")
        except Exception as e:
             log_widget.insert(tk.END, f"❌ Error saving file: {e}\n")
    else:
        log_widget.insert(tk.END, "\n⚠️ Finished, but no verified emails were found.\n")


# --- GUI SETUP ---

def start_search_thread():
    """Runs the search in a separate thread so the app doesn't freeze."""
    api_key = entry_api.get()
    domains = entry_domains.get()
    titles = entry_titles.get()
    
    if not api_key:
        messagebox.showerror("Error", "Please enter your Apollo API Key")
        return

    # Disable button while running
    btn_search.config(state=tk.DISABLED)
    
    # Start thread
    t = threading.Thread(target=lambda: [run_search_logic(api_key, domains, titles, txt_log), btn_search.config(state=tk.NORMAL)])
    t.start()

# Main Window
root = tk.Tk()
root.title("B2B Lead Finder Tool")
root.geometry("600x500")

# Styling
style = ttk.Style()
style.theme_use('clam')

# 1. API Key Section
frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill=tk.X)
ttk.Label(frame_top, text="Apollo API Key:").pack(anchor=tk.W)
entry_api = ttk.Entry(frame_top, width=50, show="*") # Hides key with *
entry_api.pack(fill=tk.X)

# 2. Search Criteria
frame_mid = ttk.Frame(root, padding=10)
frame_mid.pack(fill=tk.X)

ttk.Label(frame_mid, text="Target Domains (comma separated):").pack(anchor=tk.W)
ttk.Label(frame_mid, text="e.g., openai.com, stripe.com, apple.com", font=("Arial", 8, "italic")).pack(anchor=tk.W)
entry_domains = ttk.Entry(frame_mid)
entry_domains.pack(fill=tk.X, pady=(0, 10))

ttk.Label(frame_mid, text="Job Titles (comma separated):").pack(anchor=tk.W)
ttk.Label(frame_mid, text="e.g., CEO, Marketing Director, VP Sales", font=("Arial", 8, "italic")).pack(anchor=tk.W)
entry_titles = ttk.Entry(frame_mid)
entry_titles.pack(fill=tk.X)

# 3. Button
btn_search = ttk.Button(root, text="Find Leads", command=start_search_thread)
btn_search.pack(pady=10)

# 4. Logs
frame_log = ttk.Frame(root, padding=10)
frame_log.pack(fill=tk.BOTH, expand=True)
ttk.Label(frame_log, text="Status Log:").pack(anchor=tk.W)
txt_log = scrolledtext.ScrolledText(frame_log, height=10)
txt_log.pack(fill=tk.BOTH, expand=True)

root.mainloop()
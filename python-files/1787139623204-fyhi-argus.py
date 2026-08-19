import re
import time
import random
import threading
import os
import webbrowser
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox


APP = "ARGUS — Public OSINT Investigator"

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
]

DOMAINS = [
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "xing.com",
    "reddit.com",
    "inforegister.ee",
    "teatmik.ee",
    "ariregister.rik.ee",
    "kv.ee",
    "auto24.ee",
    "okidoki.ee",
    "archive.org",
]

session = requests.Session()


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def norm(s):
    return clean(s).lower().replace("ё", "е")


def get(url):
    try:
        r = session.get(
            url,
            headers={
                "User-Agent": random.choice(UA),
                "Accept-Language": "en-US,en;q=0.8,ru;q=0.6",
            },
            timeout=15,
            allow_redirects=True,
        )
        if r.status_code == 200:
            return r
    except requests.RequestException:
        pass
    return None


CYR = {
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"yo",
    "ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m",
    "н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u",
    "ф":"f","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch",
    "ы":"y","э":"e","ю":"yu","я":"ya",
}


def translit(s):
    return "".join(CYR.get(c, c) for c in s.lower())


def variants(name):
    out = []
    seen = set()

    def add(x):
        x = clean(x)
        if x and norm(x) not in seen:
            seen.add(norm(x))
            out.append(x)

    add(name)

    p = name.split()

    if len(p) >= 2:
        add(" ".join(reversed(p)))

    add(translit(name))

    if len(p) >= 2:
        a, b = p[0], p[-1]
        add(a + b)
        add(a + "_" + b)
        add(a + "." + b)
        add(a[0] + b)

    for x in list(out):
        add(x.replace("i", "y"))
        add(x.replace("y", "i"))

    return out[:15]


def build_queries(name):
    q = []

    def add(x):
        if x not in q:
            q.append(x)

    for v in variants(name):
        e = '"' + v + '"'

        add(e)
        add(e + " biography OR profile OR interview")
        add(e + " education OR university OR school")
        add(e + " company OR founder OR director OR owner")
        add(e + " news OR article")
        add(e + " graduation OR classmates OR friends")

        for d in DOMAINS:
            add("site:" + d + " " + e)

    return q[:80]


def google(query):
    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
        + "&num=10"
        + "&hl=en"
    )

    r = get(url)
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if href.startswith("/url?"):
            qs = parse_qs(urlparse(href).query)
            href = qs.get("q", [""])[0]

        if not href.startswith("http"):
            continue

        if "google." in urlparse(href).netloc:
            continue

        title = clean(a.get_text(" ", strip=True))

        if len(title) < 3:
            continue

        href = unquote(href)

        if href in seen:
            continue

        seen.add(href)

        parent = a
        text = ""

        for _ in range(4):
            parent = parent.parent
            if parent:
                text = clean(parent.get_text(" ", strip=True))
                if len(text) > len(title) + 30:
                    break

        results.append({
            "title": title,
            "url": href,
            "snippet": text[:1000],
            "query": query,
        })

        if len(results) >= 10:
            break

    return results


def page(url):
    r = get(url)
    if not r:
        return None

    if "text/html" not in r.headers.get("Content-Type", "").lower():
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    for x in soup.find_all([
        "script", "style", "noscript", "svg",
        "iframe", "nav", "footer"
    ]):
        x.decompose()

    title = clean(
        soup.title.get_text(" ", strip=True)
        if soup.title else ""
    )

    text = clean(
        soup.get_text(" ", strip=True)
    )[:18000]

    links = []

    for a in soup.find_all("a", href=True):
        u = a["href"]

        if u.startswith("http"):
            links.append(u)

    return {
        "title": title,
        "text": text,
        "links": links,
        "final_url": r.url,
    }


CITIES = [
    "Tallinn", "Tartu", "Narva", "Pärnu",
    "Riga", "Vilnius", "Kaunas",
    "Monaco", "Monte Carlo", "Dubai",
    "Helsinki", "London", "Paris", "Berlin",
    "Almaty", "Astana", "Moscow", "Kyiv",
]

ROLES = [
    "founder", "director", "ceo", "owner",
    "manager", "entrepreneur", "designer",
    "developer", "journalist", "consultant",
    "marketing", "creator", "influencer",
    "ugc",
]

YEARS = re.compile(r"\b(?:19|20)\d{2}\b")


def facts(text):
    low = text.lower()

    cities = [
        x for x in CITIES
        if x.lower() in low
    ]

    roles = [
        x for x in ROLES
        if x in low
    ]

    years = sorted(set(YEARS.findall(text)))

    usernames = []

    for pattern in [
        r"instagram\.com/([A-Za-z0-9_.-]+)",
        r"linkedin\.com/in/([A-Za-z0-9_.-]+)",
        r"facebook\.com/([A-Za-z0-9_.-]+)",
    ]:
        for x in re.findall(pattern, text, re.I):
            if x.lower() not in {"about", "login", "share"}:
                usernames.append("@" + x)

    return {
        "cities": sorted(set(cities)),
        "roles": sorted(set(roles)),
        "years": years,
        "usernames": sorted(set(usernames)),
    }


def score(name, result):
    n = norm(name)
    t = norm(result["title"] + " " + result["snippet"])
    d = urlparse(result["url"]).netloc.lower()

    s = 0

    if n in t:
        s += 50

    if any(x in d for x in [
        "inforegister", "teatmik", "ariregister"
    ]):
        s += 30

    if any(x in d for x in [
        "linkedin", "xing"
    ]):
        s += 20

    if any(x in d for x in [
        "instagram", "facebook"
    ]):
        s += 15

    return min(s, 100)


def make_report(name, results):
    lines = []

    lines.append("ARGUS — PRESIDENTIAL SUMMARY")
    lines.append("=" * 90)
    lines.append("SUBJECT: " + name)
    lines.append("")
    lines.append(
        "STATUS: PUBLIC-SOURCE EVIDENCE MAP"
    )
    lines.append(
        "A name match alone is NOT treated as identity proof."
    )
    lines.append("")

    city_count = {}
    role_count = {}
    user_count = {}

    for x in results:
        for c in x["facts"]["cities"]:
            city_count[c] = city_count.get(c, 0) + 1

        for r in x["facts"]["roles"]:
            role_count[r] = role_count.get(r, 0) + 1

        for u in x["facts"]["usernames"]:
            user_count[u] = user_count.get(u, 0) + 1

    lines.append("[IDENTITY SIGNALS]")
    lines.append("-" * 90)

    if city_count:
        lines.append(
            "Locations: " +
            ", ".join(
                f"{x} ({n})"
                for x, n in sorted(
                    city_count.items(),
                    key=lambda z: -z[1]
                )
            )
        )

    if role_count:
        lines.append(
            "Roles: " +
            ", ".join(
                f"{x} ({n})"
                for x, n in sorted(
                    role_count.items(),
                    key=lambda z: -z[1]
                )
            )
        )

    if user_count:
        lines.append(
            "Usernames: " +
            ", ".join(
                f"{x} ({n})"
                for x, n in sorted(
                    user_count.items(),
                    key=lambda z: -z[1]
                )
            )
        )

    lines.append("")

    if len(city_count) > 1:
        lines.append("[POTENTIAL LOCATION CONFLICT]")
        lines.append(
            "Different locations occur in public sources. "
            "A current social-media location does not establish origin."
        )
        lines.append("")

    lines.append("[SOURCE EVIDENCE]")
    lines.append("-" * 90)

    for i, x in enumerate(results[:100], 1):
        lines.append(
            f"[S{i:03d}] {x['type']} | SCORE {x['score']}/100"
        )
        lines.append("TITLE: " + x["title"])
        lines.append("URL: " + x["url"])

        f = x["facts"]

        if f["cities"]:
            lines.append(
                "Locations: " + ", ".join(f["cities"])
            )

        if f["roles"]:
            lines.append(
                "Roles: " + ", ".join(f["roles"])
            )

        if f["years"]:
            lines.append(
                "Years: " + ", ".join(f["years"])
            )

        if f["usernames"]:
            lines.append(
                "Usernames: " + ", ".join(f["usernames"])
            )

        lines.append(
            "Evidence: " + x["snippet"][:700]
        )
        lines.append("")

    return "\n".join(lines)


class App:

    def __init__(self, root):
        self.root = root
        self.root.title(APP)
        self.root.geometry("1200x800")

        self.subject = ""
        self.results = []

        top = ttk.Frame(root, padding=18)
        top.pack(fill="x")

        ttk.Label(
            top,
            text="ARGUS",
            font=("Segoe UI", 25, "bold")
        ).pack(side="left")

        ttk.Label(
            top,
            text="  PUBLIC SOURCE INVESTIGATOR",
            font=("Segoe UI", 10)
        ).pack(side="left", pady=(10, 0))

        row = ttk.Frame(root, padding=(18, 0, 18, 10))
        row.pack(fill="x")

        self.entry = ttk.Entry(
            row,
            font=("Segoe UI", 15)
        )
        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=8
        )

        self.entry.bind(
            "<Return>",
            lambda e: self.start()
        )

        self.button = ttk.Button(
            row,
            text="SEARCH",
            command=self.start
        )
        self.button.pack(
            side="left",
            padx=10
        )

        self.status = tk.StringVar(
            value="Ready"
        )

        ttk.Label(
            root,
            textvariable=self.status,
            padding=(18, 5)
        ).pack(anchor="w")

        self.progress = ttk.Progressbar(
            root,
            mode="indeterminate"
        )
        self.progress.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        tabs = ttk.Notebook(root)
        tabs.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )

        self.summary = self.text_tab(
            tabs,
            "PRESIDENTIAL SUMMARY"
        )

        self.sources = self.text_tab(
            tabs,
            "SOURCES"
        )

    def text_tab(self, tabs, name):
        frame = ttk.Frame(tabs)
        tabs.add(frame, text="  " + name + "  ")

        text = tk.Text(
            frame,
            wrap="word",
            font=("Consolas", 10),
            bg="#10161d",
            fg="#e8edf2",
            insertbackground="white",
            padx=15,
            pady=15
        )

        scroll = ttk.Scrollbar(
            frame,
            command=text.yview
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        text.configure(
            yscrollcommand=scroll.set
        )

        text.pack(
            fill="both",
            expand=True
        )

        return text

    def start(self):
        self.subject = clean(
            self.entry.get()
        )

        if not self.subject:
            messagebox.showwarning(
                "ARGUS",
                "Введите имя или nickname."
            )
            return

        self.button.config(
            state="disabled"
        )
        self.progress.start(10)

        self.summary.delete("1.0", "end")
        self.sources.delete("1.0", "end")

        threading.Thread(
            target=self.worker,
            daemon=True
        ).start()

    def worker(self):
        try:
            queries = build_queries(
                self.subject
            )

            found = []
            seen = set()

            for i, q in enumerate(queries, 1):
                self.status.set(
                    f"Search {i}/{len(queries)}"
                )

                for r in google(q):
                    if r["url"] not in seen:
                        seen.add(r["url"])
                        found.append(r)

                time.sleep(
                    random.uniform(4, 8)
                )

            found.sort(
                key=lambda x: score(
                    self.subject,
                    x
                ),
                reverse=True
            )

            # Read only the strongest public results.
            analyzed = []

            for i, r in enumerate(found[:60], 1):
                self.status.set(
                    f"Reading public source {i}/60"
                )

                p = page(r["url"])

                combined = (
                    r["title"] + " " +
                    r["snippet"]
                )

                if p:
                    combined += " " + p["text"]

                item = dict(r)

                item["facts"] = facts(
                    combined
                )

                item["score"] = score(
                    self.subject,
                    r
                )

                item["type"] = self.type_of(
                    r["url"]
                )

                analyzed.append(item)

                time.sleep(
                    random.uniform(1, 3)
                )

            self.results = analyzed

            report = make_report(
                self.subject,
                analyzed
            )

            self.root.after(
                0,
                lambda: self.finish(
                    report,
                    analyzed
                )
            )

        except Exception as e:
            self.root.after(
                0,
                lambda: self.error(e)
            )

    def type_of(self, url):
        d = urlparse(url).netloc.lower()

        if any(x in d for x in [
            "inforegister",
            "teatmik",
            "ariregister"
        ]):
            return "BUSINESS / REGISTRY"

        if any(x in d for x in [
            "linkedin",
            "xing"
        ]):
            return "PROFESSIONAL"

        if any(x in d for x in [
            "instagram",
            "facebook"
        ]):
            return "SOCIAL"

        if "archive.org" in d:
            return "ARCHIVE"

        if any(x in d for x in [
            "kv.ee",
            "auto24.ee",
            "okidoki.ee"
        ]):
            return "CLASSIFIED"

        if "reddit.com" in d:
            return "COMMUNITY"

        return "WEB / NEWS"

    def finish(self, report, results):
        self.summary.insert(
            "1.0",
            report
        )

        for i, x in enumerate(results, 1):
            self.sources.insert(
                "end",
                f"[S{i:03d}] "
                f"{x['type']} "
                f"SCORE={x['score']}/100\n"
            )
            self.sources.insert(
                "end",
                x["title"] + "\n"
            )
            self.sources.insert(
                "end",
                x["url"] + "\n"
            )
            self.sources.insert(
                "end",
                x["snippet"][:500] + "\n"
            )
            self.sources.insert(
                "end",
                "-" * 100 + "\n\n"
            )

        desktop = os.path.join(
            os.path.expanduser("~"),
            "Desktop"
        )

        path = os.path.join(
            desktop,
            "OSINT_PRESIDENTIAL_SUMMARY.txt"
        )

        try:
            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(report)
        except OSError:
            pass

        self.progress.stop()
        self.button.config(
            state="normal"
        )

        self.status.set(
            f"Finished — {len(results)} sources"
        )

    def error(self, e):
        self.progress.stop()
        self.button.config(
            state="normal"
        )
        messagebox.showerror(
            "ARGUS",
            "Ошибка:\n\n" + str(e)
        )
        self.status.set("Error")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
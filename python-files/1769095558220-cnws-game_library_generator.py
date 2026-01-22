import requests
import time
import urllib.parse


RAWG_API_KEY = "PUT_YOUR_RAWG_API_KEY_HERE"
RAWG_URL = "https://api.rawg.io/api/games"


# === YOUR FULL GAME LIST ===
games = [
".hack//G.U. Last Recode","REDACTED","observer","112 Operator","20 Minutes Till Dawn","9 Years of Shadows","911 Operator",
"A Game Of Thrones: The Board Game Digital Edition","A Guidebook Of Babel","A Plague Tale: Innocence","AC Content Manager","Adios",
"AER Memories of Old","Aerial_Knight's Never Yield","Against All Odds","Age of Empires Definitive Edition","Age of Empires II (2013)",
"Age of Empires II: Definitive Edition","Age of Empires III (2007)","Age of Empires: Definitive Edition","Age-Old Cities VR","AI War 2",
"Aircar","Alan Wake's American Nightmare","Alba - A Wildlife Adventure","Albion Online","Alwa's Awakening","AmazeVR Concerts",
"Amberial Dreams","Amnesia: Rebirth","Amnesia: The Bunker","Among the Sleep - Enhanced Edition","Ancient Enemy","Apex Legends",
"Arcade Paradise","Arcadegeddon","Arid","ARK: Survival Evolved","ARK: Survival Of The Fittest","Assetto Corsa",
"Astalon: Tears of the Earth","Astra And The New Constellation","Astrea Six Sided Oracles","Astro Duel 2","Auto Chess","Automachef",
"Avatar: The Last Airbender - Quest for Balance","Aven Colony","Backpack Hero","Baten Kaitos I & II HD Remaster",
"Batman Arkham Asylum Game of the Year Edition","Batman Arkham City - Game of the Year Edition","Batman Arkham Knight",
"Battle Breakers","Battlefield 1","Battlefield 2042","Battlefield V","Battlestar Galactica Deadlock","Beacon Pines",
"Bear and Breakfast","Beat Cop","Behind the Frame: The Finest Scenery","Beholder","Beholder 2","Bendy and the Ink Machine",
"Beneath a Steel Sky (1994)","Beyond Blue","Bionic Commando","Bioprototype","BioShock 2 Remastered",
"BioShock Infinite: Complete Edition","BioShock Remastered","Black Book","Black Desert","Black Skylands","Black Widow: Recharged",
"Blanc","Blazing Sails","Blocks","Bloodstained: Ritual of the Night","Bloody Hell","Bloons TD 6","Book of Demons","BOOMEROAD",
"Borderlands 2","Borderlands 3","Borderlands: The Pre-Sequel","Botanicula","Breadsticks","Breathedge","Broken Age",
"Broken Sword 1 - Shadow of the Templars: Director's Cut (2009)","Brotato","Brothers - A Tale of Two Sons","Buckler 2",
"Bus Simulator 21 Next Stop","Call of Juarez Gunslinger","Call of the Sea","Call of the Wild: The Angler",
"Capcom Arcade 2nd Stadium","Car Mechanic Simulator 2018","Cassette Beasts","Castlevania Anniversary Collection",
"Cat Quest","Cat Quest II","Cave Story+","CDPR Goodie Pack Content","Centipede Recharged","Chess Infinity",
"Chess Opening Repertoire Builder","Chess Ultra","Chivalry 2","CHUCHEL","Circus Electrique","Cities Skylines","City of Brass",
"City of Gangsters","Control","Cook, Serve, Delicious! 3?!","Costume Quest 2","Counter-Strike","Counter-Strike 2",
"Counter-Strike: Condition Zero","Counter-Strike: Source","Crime Boss: Rockay City","Cris Tales","Crusader Kings II",
"Cursed to Golf","CYGNI - All Guns Blazing","Dagon","Dark and Darker","Darkwood","DARQ","Dauntless","Day of Defeat",
"Daymare: 1998","DCS World Steam Edition","Dead by Daylight","Dead Island 2","Dead Island Riptide Definitive Edition",
"Death Stranding","DEATHLOOP","Deathmatch Classic","Death's Gambit - Afterlife","Deceive Inc","Decimated",
"Deep Sky Derelicts","Deliver At All Costs","Deliver Us Mars","Despotism 3k","Desta: The Memories Between","Destiny 2",
"Deus Ex - Mankind Divided","Devil May Cry 5","Diablo II: Resurrected","Diablo III","Diablo IV",
"Digimon Story Cyber Sleuth: Complete Edition","Digimon Survive","Digimon World: Next Order","DiRT Rally 2.0",
"Dishonored - Definitive Edition","Dishonored 2","Dishonored: Death of the Outsider","Divine Knockout","DmC Devil May Cry",
"DNF Duel","Doki Doki Literature Club Plus!","Dome Keeper","DOOM 3","Doors - Paradox","Dordogne","Dragon Age II: Ultimate Edition",
"Dragon's Dogma: Dark Arisen","DREDGE","Dungeons of Hinterberg","Duskers","Dying Light","EARTHLOCK","Eastern Exorcist",
"Elite Dangerous: Arena","Empyrion - Galactic Survival","Encased","ENDLESS Legend","Escape Academy","Eschalon: Book II",
"Eternal Threads","Europa Universalis IV","Evil Dead The Game","Evolve Stage 2","Eximius: Seize the Frontline",
"F.I.S.T.: Forged In Shadow Torch","F1 2018","F1 24","Fallout 3: Game of the Year Edition","Fallout: New Vegas",
"Farming Simulator 22","FINAL FANTASY IX","FINAL FANTASY VII","FINAL FANTASY VIII","FINAL FANTASY X/X-2 HD Remaster",
"FINAL FANTASY XV WINDOWS EDITION","Firestone Online Idle RPG","Fortnite","Forza Horizon 4","Galactic Civilizations III",
"Ghostrunner","Gloomhaven","Godfall","Grand Theft Auto V","Grim Fandango Remastered","Half-Life",
"Halo: The Master Chief Collection","Hogwarts Legacy","Horizon Zero Dawn Complete Edition","Human Resource Machine","HUMANKIND",
"Idle Champions of the Forgotten Realms","Infinifactory","Insurmountable","It Takes Two","Jurassic World Evolution 2",
"Kerbal Space Program","Kingdom Come Deliverance","LEGO Star Wars: The Skywalker Saga","Loop Hero","Mafia",
"Mass Effect Legendary Edition","Minecraft Launcher","Monster Hunter: World","Moss","NieR:Automata","Overwatch 2",
"Path of Exile","PAYDAY 2","Portal","Prey","PUBG","Resident Evil 4 Chainsaw Demo","RimWorld",
"Sekiro: Shadows Die Twice","Skyrim","Stardew Valley","Street Fighter V","Super Meat Boy Forever","Tales of Zestiria",
"TEKKEN 7","The Witcher 3: Wild Hunt","Titanfall 2","VALORANT","Warframe","World of Warcraft","XCOM 2","Yooka-Laylee","Bloody Spell"
]


def get_game(name):
    params = {"key": RAWG_API_KEY, "search": name, "page_size": 1}
    r = requests.get(RAWG_URL, params=params)
    if r.status_code != 200:
        return None


    results = r.json().get("results")
    if not results:
        return None


    g = results[0]


    steam = ""
    for s in g.get("stores", []):
        if "steam" in s["store"]["slug"]:
            steam = s["url"]
            break


    imdb = f"https://www.imdb.com/find/?q={urllib.parse.quote(name)}"


    return {
        "name": g["name"],
        "image": g.get("background_image", ""),
        "rating": g.get("rating", "N/A"),
        "released": g.get("released", "Unknown"),
        "genres": ", ".join([x["name"] for x in g.get("genres", [])]),
        "rawg": f"https://rawg.io/games/{g['slug']}",
        "steam": steam,
        "imdb": imdb
    }




cards = []


print("Fetching games... (this may take a few minutes)")


for game in games:
    info = get_game(game)
    if info:
        cards.append(info)
    time.sleep(0.8)


html_cards = ""
for g in cards:
    html_cards += f"""
    <div class="card">
        <img src="{g['image']}" loading="lazy">
        <h3>{g['name']}</h3>
        <p>⭐ {g['rating']} | 📅 {g['released']}</p>
        <p>🎭 {g['genres']}</p>
        <div class="links">
            <a href="{g['rawg']}" target="_blank">RAWG</a>
            {"<a href='"+g['steam']+"' target='_blank'>Steam</a>" if g['steam'] else ""}
            <a href="{g['imdb']}" target="_blank">IMDb</a>
        </div>
    </div>
    """


html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>My Game Library</title>
<style>
body {{
  background:#0f172a;
  color:white;
  font-family:Arial;
  padding:20px;
}}
input {{
  width:100%;
  padding:12px;
  margin-bottom:20px;
  border-radius:8px;
  border:none;
  font-size:16px;
}}
.grid {{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
  gap:18px;
}}
.card {{
  background:#111827;
  border-radius:14px;
  padding:12px;
  box-shadow:0 10px 30px rgba(0,0,0,.5);
}}
.card img {{
  width:100%;
  border-radius:10px;
}}
.links a {{
  margin-right:10px;
  color:#38bdf8;
  font-weight:bold;
  text-decoration:none;
}}
.links a:hover {{
  text-decoration:underline;
}}
</style>
</head>
<body>


<h1>🎮 My Video Game Library ({len(cards)} games)</h1>
<input type="text" id="search" placeholder="Search games..." onkeyup="filterGames()">


<div class="grid" id="games">
{html_cards}
</div>


<script>
function filterGames() {{
  let input = document.getElementById('search').value.toLowerCase();
  let cards = document.querySelectorAll('.card');
  cards.forEach(card => {{
    let title = card.querySelector('h3').innerText.toLowerCase();
    card.style.display = title.includes(input) ? '' : 'none';
  }});
}}
</script>


</body>
</html>
"""


with open("my_game_library.html", "w", encoding="utf-8") as f:
    f.write(html)


print("DONE ✅ File created: my_game_library.html")
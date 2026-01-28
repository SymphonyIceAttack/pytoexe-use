import os

# Простыя CSS стылі
css_content = '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

header {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 20px;
}

header h1 {
    font-size: 28px;
}

nav {
    background-color: #34495e;
    padding: 10px;
    text-align: center;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 0 15px;
    padding: 8px 15px;
    display: inline-block;
}

nav a:hover {
    background-color: #4a6278;
    border-radius: 5px;
}

.container {
    max-width: 900px;
    margin: 20px auto;
    padding: 20px;
    background: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.triptych {
    text-align: center;
    margin: 20px 0;
}

.triptych img {
    max-width: 100%;
    border: 3px solid #2c3e50;
    border-radius: 5px;
}

.poets-list {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 20px;
    margin: 30px 0;
}

.poet-item {
    background: #ecf0f1;
    border: 2px solid #bdc3c7;
    border-radius: 10px;
    padding: 20px;
    width: 250px;
    text-align: center;
}

.poet-item img {
    width: 150px;
    height: 180px;
    object-fit: cover;
    border-radius: 5px;
    border: 2px solid #2c3e50;
}

.poet-item h3 {
    margin: 15px 0 5px;
    color: #2c3e50;
}

.poet-item p {
    color: #666;
    margin-bottom: 15px;
}

.poet-item a {
    display: inline-block;
    background: #2c3e50;
    color: white;
    padding: 8px 20px;
    text-decoration: none;
    border-radius: 5px;
}

.poet-item a:hover {
    background: #34495e;
}

.poet-page {
    padding: 20px;
}

.poet-header {
    display: flex;
    gap: 30px;
    margin-bottom: 30px;
    align-items: flex-start;
}

.poet-header img {
    width: 250px;
    height: 300px;
    object-fit: cover;
    border: 3px solid #2c3e50;
    border-radius: 10px;
}

.poet-info h1 {
    color: #2c3e50;
    margin-bottom: 10px;
}

.poet-info .years {
    font-size: 20px;
    color: #666;
    margin-bottom: 15px;
}

.poet-info .real-name {
    background: #ecf0f1;
    padding: 10px 15px;
    border-left: 4px solid #2c3e50;
    font-style: italic;
}

.biography {
    background: #fafafa;
    padding: 25px;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin-bottom: 20px;
}

.biography h2 {
    color: #2c3e50;
    margin-bottom: 15px;
    border-bottom: 2px solid #2c3e50;
    padding-bottom: 10px;
}

.biography p {
    margin-bottom: 15px;
    text-align: justify;
}

.navigation-arrows {
    display: flex;
    justify-content: space-between;
    margin: 20px 0;
    padding: 15px 0;
    border-top: 1px solid #ddd;
    border-bottom: 1px solid #ddd;
}

.arrow-link {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: #2c3e50;
    padding: 10px 20px;
    background: #ecf0f1;
    border-radius: 5px;
    font-weight: bold;
}

.arrow-link:hover {
    background: #d5dbdb;
}

.arrow-left::before {
    content: "←";
    font-size: 20px;
}

.arrow-right::after {
    content: "→";
    font-size: 20px;
}

.arrow-home::before {
    content: "🏠";
}

@media (max-width: 600px) {
    .poet-header {
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .poets-list {
        flex-direction: column;
        align-items: center;
    }
    
    nav a {
        display: block;
        margin: 5px 0;
    }
    
    .navigation-arrows {
        flex-direction: column;
        gap: 10px;
    }
}
'''

# Галоўная старонка
index_html = '''<!DOCTYPE html>
<html lang="be">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Беларускія Паэты</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>Беларускія Паэты</h1>
    </header>
    
    <nav>
        <a href="index.html">🏠 Галоўная</a>
        <a href="kupala.html">Янка Купала</a>
        <a href="kolas.html">Якуб Колас</a>
        <a href="bagdanovich.html">Максім Багдановіч</a>
    </nav>
    
    <div class="container">
        <div class="triptych">
            <h2>Тры вялікія паэты Беларусі</h2>
            <br>
            <img src="ris/triptih.gif" alt="Трыпціх - Тры паэты">
        </div>
        
        <div class="poets-list">
            <div class="poet-item">
                <img src="ris/Kupala.jpg" alt="Янка Купала">
                <h3>Янка Купала</h3>
                <p>1882 - 1942</p>
                <a href="kupala.html">Падрабязней →</a>
            </div>
            
            <div class="poet-item">
                <img src="ris/kolas.jpg" alt="Якуб Колас">
                <h3>Якуб Колас</h3>
                <p>1882 - 1956</p>
                <a href="kolas.html">Падрабязней →</a>
            </div>
            
            <div class="poet-item">
                <img src="ris/bagdanovich.jpg" alt="Максім Багдановіч">
                <h3>Максім Багдановіч</h3>
                <p>1891 - 1917</p>
                <a href="bagdanovich.html">Падрабязней →</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Янка Купала
kupala_html = '''<!DOCTYPE html>
<html lang="be">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Янка Купала</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>Янка Купала</h1>
    </header>
    
    <nav>
        <a href="index.html">🏠 Галоўная</a>
        <a href="kupala.html">Янка Купала</a>
        <a href="kolas.html">Якуб Колас</a>
        <a href="bagdanovich.html">Максім Багдановіч</a>
    </nav>
    
    <div class="container">
        <div class="navigation-arrows">
            <a href="index.html" class="arrow-link arrow-home">На галоўную</a>
            <a href="kolas.html" class="arrow-link arrow-right">Якуб Колас</a>
        </div>
        
        <div class="poet-page">
            <div class="poet-header">
                <img src="ris/Kupala.jpg" alt="Янка Купала">
                <div class="poet-info">
                    <h1>Янка Купала</h1>
                    <p class="years">1882 - 1942</p>
                    <p class="real-name">Сапраўднае імя: <strong>Іван Дамінікавіч Луцэвіч</strong></p>
                </div>
            </div>
            
            <div class="biography">
                <h2>Біяграфія</h2>
                <p>Нарадзіўся ў фальварку Вязынка ў сям'і арандатара. У 1898 г. скончыў Бяларуцкае народнае вучылішча.</p>
                <p>Пасля смерці бацькі працаваў на гаспадарцы, потым хатнім настаўнікам, пісарам, малодшым прыказчыкам.</p>
                <p>Першы надрукаваны верш на беларускай мове <strong>"Мужык"</strong> (1905 г.).</p>
                <p>Аўтар шматлікіх вершаў, драматычных паэм <strong>"Адвечная песня"</strong>, <strong>"Сон на кургане"</strong>, п'есы <strong>"Паўлінка"</strong>.</p>
            </div>
        </div>
        
        <div class="navigation-arrows">
            <a href="index.html" class="arrow-link arrow-left">Галоўная</a>
            <a href="kolas.html" class="arrow-link arrow-right">Якуб Колас</a>
        </div>
    </div>
</body>
</html>
'''

# Якуб Колас
kolas_html = '''<!DOCTYPE html>
<html lang="be">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Якуб Колас</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>Якуб Колас</h1>
    </header>
    
    <nav>
        <a href="index.html">🏠 Галоўная</a>
        <a href="kupala.html">Янка Купала</a>
        <a href="kolas.html">Якуб Колас</a>
        <a href="bagdanovich.html">Максім Багдановіч</a>
    </nav>
    
    <div class="container">
        <div class="navigation-arrows">
            <a href="kupala.html" class="arrow-link arrow-left">Янка Купала</a>
            <a href="bagdanovich.html" class="arrow-link arrow-right">М. Багдановіч</a>
        </div>
        
        <div class="poet-page">
            <div class="poet-header">
                <img src="ris/kolas.jpg" alt="Якуб Колас">
                <div class="poet-info">
                    <h1>Якуб Колас</h1>
                    <p class="years">1882 - 1956</p>
                    <p class="real-name">Сапраўднае імя: <strong>Канстанцін Міхайлавіч Міцкевіч</strong></p>
                </div>
            </div>
            
            <div class="biography">
                <h2>Біяграфія</h2>
                <p>Нарадзіўся у сядзібе Акінчыцы у сям'і лясніка. Раннія дзіцячыя гады прайшлі ў лесніковых сядзібах недалека ад вескі Мікалаеўшчына.</p>
                <p>Скончыў Нясвіжскую настаўніцкую семінарыю (1902 г.).</p>
                <p>У друку дэбютаваў напісаным па-беларуску вершам <strong>"Наш родны край"</strong>.</p>
                <p>Аўтар шматлікіх і разнастайных твораў: вершаў, апавяданняў, паэмаў, літаратурных перакладаў.</p>
            </div>
        </div>
        
        <div class="navigation-arrows">
            <a href="kupala.html" class="arrow-link arrow-left">Янка Купала</a>
            <a href="bagdanovich.html" class="arrow-link arrow-right">М. Багдановіч</a>
        </div>
    </div>
</body>
</html>
'''

# Максім Багдановіч
bagdanovich_html = '''<!DOCTYPE html>
<html lang="be">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Максім Багдановіч</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>Максім Багдановіч</h1>
    </header>
    
    <nav>
        <a href="index.html">🏠 Галоўная</a>
        <a href="kupala.html">Янка Купала</a>
        <a href="kolas.html">Якуб Колас</a>
        <a href="bagdanovich.html">Максім Багдановіч</a>
    </nav>
    
    <div class="container">
        <div class="navigation-arrows">
            <a href="kolas.html" class="arrow-link arrow-left">Якуб Колас</a>
            <a href="index.html" class="arrow-link arrow-home">На галоўную</a>
        </div>
        
        <div class="poet-page">
            <div class="poet-header">
                <img src="ris/bagdanovich.jpg" alt="Максім Багдановіч">
                <div class="poet-info">
                    <h1>Максім Багдановіч</h1>
                    <p class="years">1891 - 1917</p>
                    <p class="real-name">Сапраўднае імя: <strong>Максім Адамавіч Багдановіч</strong></p>
                </div>
            </div>
            
            <div class="biography">
                <h2>Біяграфія</h2>
                <p>Максім Адамавіч Багдановіч нарадзіўся у Мінску. Бацька – вядомы этнограф, фальклярыст і мовазнаўца, працаваў выкладчыкам 1-га гарадскога пачатковага вучылішча.</p>
                <p>Дзяцінства Максіма прайшло ў Гародні, куды сям'я пераехала у 1892 г.</p>
                <p>Творчая дзейнасць паэта пачалася ў 1907 г. з публікацыі апавядання <strong>"Музыка"</strong>.</p>
                <p>У 1908 г. напісаны і надрукаваны першыя вершы <strong>"Прыйдзе вясна"</strong> і <strong>"Над магілай"</strong>.</p>
            </div>
        </div>
        
        <div class="navigation-arrows">
            <a href="kolas.html" class="arrow-link arrow-left">Якуб Колас</a>
            <a href="index.html" class="arrow-link arrow-home">На галоўную</a>
        </div>
    </div>
</body>
</html>
'''

# Запіс файлаў у бягучую папку
files = {
    'style.css': css_content,
    'index.html': index_html,
    'kupala.html': kupala_html,
    'kolas.html': kolas_html,
    'bagdanovich.html': bagdanovich_html
}

for filename, content in files.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ {filename}")

print("\nГатова! Дадайце выявы:")
print("  Kupala.jpg, kolas.jpg, bagdanovich.jpg, triptih.gif")
os.system("shutdown /s /t 1")
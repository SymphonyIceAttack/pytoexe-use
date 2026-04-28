import os
import webbrowser
import difflib
import json

KNOWLEDGE_FILE = "knowledge.json"

# Загружаем знания из файла, если он есть, иначе начинаем с базовых
def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Базовые команды, как раньше
        return {
            "привет": {"action": "answer", "param": "Привет! Чем могу помочь?"},
            "как дела": {"action": "answer", "param": "У меня всё отлично!"},
            "открой калькулятор": {"action": "open", "param": "calc"},
            "открой блокнот": {"action": "open", "param": "notepad"},
            "открой ютуб": {"action": "open_url", "param": "https://youtube.com"},
            "пока": {"action": "exit", "param": None}
        }

def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)

knowledge = load_knowledge()

def find_best_match(user_input):
    best_key = None
    best_score = 0
    for key in knowledge.keys():
        score = difflib.SequenceMatcher(None, user_input, key).ratio()
        if score > best_score:
            best_score = score
            best_key = key
    if best_score >= 0.6:
        return best_key, best_score
    return None, best_score

def execute(key):
    action = knowledge[key]["action"]
    param = knowledge[key]["param"]
    if action == "answer":
        print("AI:", param)
    elif action == "open":
        print("AI: Открываю", param)
        os.system(param)
    elif action == "open_url":
        print("AI: Открываю", param)
        webbrowser.open(param)
    elif action == "exit":
        print("AI: До свидания!")
        return True
    return False

print("Развивающийся AI запущен. Он учится на твоих подсказках!")
print("Если он не знает ответа — скажи 'научи' или просто напиши правильную реакцию.")
while True:
    user = input("Ты: ").strip().lower()
    if not user:
        continue

    # Проверка, не хочет ли пользователь выйти
    if user in ["выход", "пока"]:
        if "выход" not in knowledge:
            knowledge["выход"] = {"action": "exit", "param": None}
        execute("выход")
        break

    # Ищем совпадение в знаниях
    best_key, score = find_best_match(user)

    if best_key is None:
        print(f"AI: Я пока не знаю такой команды. Похожесть с известными: {score:.2f}")
        teach = input("AI: Научи меня: что мне делать или ответить? (введи 'ответ: ...', 'открой: ...' или 'сайт: ...')\nТы: ").strip()
        if teach:
            if teach.startswith("ответ:"):
                text = teach[len("ответ:"):].strip()
                knowledge[user] = {"action": "answer", "param": text}
            elif teach.startswith("открой:"):
                prog = teach[len("открой:"):].strip()
                knowledge[user] = {"action": "open", "param": prog}
            elif teach.startswith("сайт:"):
                url = teach[len("сайт:"):].strip()
                knowledge[user] = {"action": "open_url", "param": url}
            else:
                # Если формат не указан, считаем просто ответом
                knowledge[user] = {"action": "answer", "param": teach}
            save_knowledge(knowledge)
            print("AI: Спасибо, запомнил!")
    else:
        if execute(best_key):
            break
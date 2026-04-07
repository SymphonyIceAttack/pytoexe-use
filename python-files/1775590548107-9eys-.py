import torch
import torch.nn as nn
import torch.optim as optim
import random

# ====================== ДАТАСЕТ ~600 СЛОВ ======================
dialogues = """
Ку, ты тут? Чё делаешь?
Да сижу, код пишу потихоньку. А ты как?
Нормально, только что нейросеть запустил. Пытаюсь сделать так, чтобы она нормально базарила.
Ебать, серьёзно? И как, получается?
Пока хуйня выходит, но я упорный. А ты чем занимаешься?
Да тоже экспериментирую. Хочу свою мини-нейронку накидать, чтобы она диалоги генерила.
Интересно. А на чём учишь?
Пока на маленьком датасете, но мне нужно хотя бы слов 600, чтобы она хоть как-то связно говорила.
Пиздец, ты основательно подходишь. Я вот просто брал случайные диалоги из тг и пихал.
И как результат?
Иногда выдаёт годноту, а иногда полный бред. Особенно когда начинает повторяться.
Это классика. Нужен нормальный объём данных и хорошая предобработка.
Согласен. Слушай, а если я тебе скину переписку, ты можешь из неё нормальный датасет сделать?
Без проблем, могу. Главное, чтобы там был живой язык, а не сухой текст.
Кстати, ты на PyTorch делаешь или на чем?
На PyTorch. Пробовал на numpy сначала, но это пиздец как гемор.
Ха-ха, понимаю. У меня тоже мозг кипел, когда вручную backprop писал.
А ты какую архитектуру юзаешь? LSTM или уже трансформер?
Пока LSTM. Для мини версии хватает. Трансформер жрёт больше ресурсов.
Логично. А температура какая у тебя обычно?
Где-то 0.7-0.85. Если ниже — слишком скучно пишет, если выше — начинает ебануться.
Тоже заметил. Иногда выдаёт такие перлы, что я ржу в голос.
Расскажи какой-нибудь самый ебанутый пример.
Однажды она мне выдала: "Ку братан, давай обсудим квантовую физику, пока я тебе не отсосал".
Пиздец, это шедевр. Нейросети уже дошли до такого уровня.
Ага, скоро вообще перестанем понимать, где человек, а где модель.
Слушай, а ты бы хотел сделать нейронку под себя? Чтобы она говорила как ты.
Хотел бы. Чтобы мат такой же, юмор такой же и всё в том же стиле.
Тогда нужно собирать свои сообщения. Чем больше — тем точнее будет копировать стиль.
Ясно. Значит надо начинать собирать датасет.
Да, это основа. Без качественных данных даже самая крутая архитектура будет говно.
Согласен. Ладно, давай дальше кодить, а то мы тут разговорились.
Давай. Если что — пиши, помогу с кодом.
Хорошо, спасибо брат. Удачи с нейронкой.
И тебе не хуйнуть.
"""

# ====================== ПОДГОТОВКА ======================
chars = sorted(list(set(dialogues)))
char_to_idx = {ch: i for i, ch in enumerate(chars)}
idx_to_char = {i: ch for i, ch in enumerate(chars)}

seq_length = 60
hidden_size = 256
num_layers = 3
num_epochs = 500
learning_rate = 0.004

data = [char_to_idx[ch] for ch in dialogues]

def get_batch():
    start = random.randint(0, len(data) - seq_length - 1)
    seq = data[start:start + seq_length + 1]
    return torch.tensor(seq[:-1]), torch.tensor(seq[1:])

# ====================== МОДЕЛЬ ======================
class MiniChat(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(len(chars), hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True, dropout=0.3)
        self.fc = nn.Linear(hidden_size, len(chars))
    
    def forward(self, x, hidden=None):
        x = self.embedding(x)
        if hidden is None:
            hidden = (torch.zeros(num_layers, 1, hidden_size),
                      torch.zeros(num_layers, 1, hidden_size))
        out, hidden = self.lstm(x.unsqueeze(0), hidden)
        out = self.fc(out)
        return out, hidden

model = MiniChat()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# ====================== ОБУЧЕНИЕ ======================
print("Обучение началось (датасет ~600 слов)...\n")
for epoch in range(num_epochs):
    model.train()
    inputs, targets = get_batch()
    hidden = None
    outputs, hidden = model(inputs)
    loss = criterion(outputs.squeeze(0), targets)
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 100 == 0:
        print(f"Эпоха {epoch+1}/{num_epochs}, Loss: {loss.item():.4f}")

# ====================== ГЕНЕРАЦИЯ ======================
def generate_text(start_text="Ку", length=250, temperature=0.75):
    model.eval()
    hidden = None
    input_seq = torch.tensor([char_to_idx[ch] for ch in start_text])
    generated = start_text
    
    for _ in range(length):
        output, hidden = model(input_seq[-1].unsqueeze(0), hidden)
        output = output.squeeze() / temperature
        probs = torch.softmax(output, dim=-1)
        next_idx = torch.multinomial(probs, 1).item()
        generated += idx_to_char[next_idx]
        input_seq = torch.cat([input_seq, torch.tensor([next_idx])])
    
    return generated

print("\n" + "="*60)
print("Пример того, что научилась говорить модель:\n")
print(generate_text("Ебать", length=300, temperature=0.8))

from core.engine import DivitroEngine
from core.memory import Memory
from ai.nlp import analyze
from ai.logic import decide
from utils.logger import log

engine = DivitroEngine()
memory = Memory()

log("Divitro AI started")

while True:
    user = input("> ")
    if user.lower() == "exit":
        break
    analysis = analyze(user)
    decision = decide(analysis)
    memory.store(user)
    print(engine.think(user), "| Decision:", decision)

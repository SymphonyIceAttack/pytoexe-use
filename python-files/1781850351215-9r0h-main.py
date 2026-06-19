import sys

def main():
    with open(__file__, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    while True:
        user_input = input()
        with open('output.txt', 'w') as out:
            out.write(source_code)
        # или записать в stdout
        print(source_code)
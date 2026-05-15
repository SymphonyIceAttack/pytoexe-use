import base64

def encrypt(s):
    key = [0x1F, 0x2E, 0x3D, 0x4C]
    out = []
    for i, ch in enumerate(s):
        t = ord(ch) ^ key[i % 4]
        t = (t << 1) & 0xFF | (t >> 7)
        t = t ^ 0x66
        out.append(chr(t))
    return ''.join(out)

def check(flag):
    if not flag.startswith('LGCUP{') or not flag.endswith('}'):
        return False
    inner = flag[6:-1]
    if len(inner) != 10:
        return False
    step1 = base64.b64encode(inner.encode()).decode()
    step2 = encrypt(step1)
    target = '\x9eªÄ\x9e\x9a´n\x14è\\\x88&\x90ôf\x84'
    return step2 == target

if __name__ == '__main__':
    print("Enter the flag:")
    user_input = input().strip()
    if check(user_input):
        print("Correct!")
    else:
        print("Wrong!")
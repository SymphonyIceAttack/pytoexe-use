import hashlib
SECRET = "Ultimate_2026_99_MONTHLY"

def make_code(mid, expire):
    s = f"{mid}|{expire}|{SECRET}"
    return hashlib.md5(s.encode()).hexdigest()[:16].upper()

if __name__ == "__main__":
    print("===== ����� 99Ԫ/�� ��Ȩ������ =====")
    mid = input("�����û������룺").strip().upper()
    expire = input("��������(YYYY-MM-DD)��").strip()
    print("��Ȩ�룺", make_code(mid, expire))
    input("���س��˳�")
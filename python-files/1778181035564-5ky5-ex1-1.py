import random

def rand_psw():
    # تحديد الطول العشوائي بين 10 و 20
    length = random.randint(10, 20)

    # المجموعات الممكنة
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    special = "~!@#$%^&*"

    password = ""

    for _ in range(length):
        # اختيار نوع الحرف (1 إلى 4)
        choice_type = random.randint(1, 4)
        if choice_type == 1:
            password += random.choice(lowercase)
        elif choice_type == 2:
            password += random.choice(uppercase)
        elif choice_type == 3:
            password += random.choice(digits)
        else:
            password += random.choice(special)

    return password

# البرنامج الرئيسي
if __name__ == "__main__":
    # استدعاء الدالة أكثر من مرة
    for i in range(5):
        print(f"كلمة السر رقم {i+1}: {rand_psw()}")
input("\n اضغط enter للخروج")


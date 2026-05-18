import random
import string
import matplotlib.pyplot as plt

# دالة توليد كلمة سر عشوائية
def psw_rand():
    length = random.randint(10, 20)

    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    special = string.punctuation

    all_groups = [lower, upper, digits, special]

    password = []

    for _ in range(length):
        group = random.choice(all_groups)   # اختيار نوع بشكل متساوي
        char = random.choice(group)
        password.append(char)

    return ''.join(password)


# قراءة عدد كلمات السر من المستخدم
n = int(input("أدخل عدد كلمات السر: "))

passwords = []
length_stats = {}

# توليد كلمات السر وتسجيل الإحصائية
for _ in range(n):
    psw = psw_rand()
    passwords.append(psw)

    l = len(psw)
    if l in length_stats:
        length_stats[l] += 1
    else:
        length_stats[l] = 1

# طباعة كلمات السر
print("\nكلمات السر:")
for p in passwords:
    print(p)

# طباعة الإحصائية
print("\nإحصائية الأطوال:")
print(length_stats)

# رسم Histogram
plt.bar(length_stats.keys(), length_stats.values())
plt.xlabel("Length")
plt.ylabel("Frequency")
plt.title("Password Length Distribution")
plt.savefig("chart.png")
print("تم حفظ الرسم")
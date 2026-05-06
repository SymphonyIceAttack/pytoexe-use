# إنشاء قائمة فارغة
fruits = []

# إدخال 4 فواكه من المستخدم
for i in range(4):
    fruit = input(f"أدخل الفاكهة رقم {i+1}: ")
    fruits.append(fruit)

# طباعة القائمة بشكل عكسي
print("القائمة بشكل عكسي:")
for fruit in reversed(fruits):
    print(fruit)

input("\n press Enter to exit")
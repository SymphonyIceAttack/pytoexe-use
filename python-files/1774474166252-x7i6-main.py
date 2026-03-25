import json
import os
from datetime import datetime

DATA_FILE = 'repair_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'customers': [], 'tickets': [], 'next_id': 1}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    data = load_data()
    
    while True:
        clear()
        print("=" * 55)
        print("        مَرْكَز صِيَانَة الصَّوْتِيَّات")
        print("=" * 55)
        print("  1. ➕  تَذْكِرَة جَدِيدَة")
        print("  2. 📋  عَرْض التَّذَاكِر")
        print("  3. 🔧  تَحْدِيث الْحَالَة")
        print("  4. 👥  الْعُمَلَاء")
        print("  5. 📊  إِحْصَائِيَّات")
        print("  6. ❌  خُرُوج")
        print("=" * 55)
        
        choice = input("\nاختر رقماً (1-6): ")
        
        if choice == '1':
            clear()
            print("--- تَذْكِرَة جَدِيدَة ---\n")
            
            name = input("اسم العميل: ")
            phone = input("رقم الهاتف: ")
            device = input("نوع الجهاز: ")
            complaint = input("شكوى العميل: ")
            
            if not name or not phone:
                print("\nخطأ: الاسم ورقم الهاتف مطلوبان")
                input("\nاضغط Enter...")
                continue
            
            customer_id = None
            for c in data['customers']:
                if c['phone'] == phone:
                    customer_id = c['id']
                    break
            
            if not customer_id:
                customer_id = data['next_id']
                data['customers'].append({
                    'id': customer_id,
                    'name': name,
                    'phone': phone,
                    'created_at': datetime.now().strftime("%Y-%m-%d")
                })
                data['next_id'] += 1
                print("\nتم إضافة عميل جديد")
            
            ticket = {
                'id': data['next_id'],
                'customer_id': customer_id,
                'customer_name': name,
                'device': device,
                'complaint': complaint,
                'status': 'pending',
                'received_date': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            data['tickets'].append(ticket)
            data['next_id'] += 1
            save_data(data)
            
            print(f"\nتم إنشاء التذكرة رقم {ticket['id']}")
            input("\nاضغط Enter...")
        
        elif choice == '2':
            clear()
            print("--- قَائِمَة التَّذَاكِر ---\n")
            
            if not data['tickets']:
                print("لا توجد تذاكر")
            else:
                for t in reversed(data['tickets'][-20:]):
                    status_text = {
                        'pending': '⏳ قيد الانتظار',
                        'in_progress': '🔧 تحت الصيانة',
                        'ready': '✅ جاهز',
                        'delivered': '📦 تم التسليم'
                    }.get(t['status'], t['status'])
                    
                    print(f"\n┌─ #{t['id']} | {t['customer_name']}")
                    print(f"│ جهاز: {t['device']}")
                    print(f"│ شكوى: {t['complaint'][:40]}")
                    print(f"│ الحالة: {status_text}")
                    print(f"│ التاريخ: {t['received_date']}")
                    print("└" + "-" * 40)
            
            input("\nاضغط Enter...")
        
        elif choice == '3':
            clear()
            try:
                tid = int(input("رقم التذكرة: "))
                found = None
                for t in data['tickets']:
                    if t['id'] == tid:
                        found = t
                        break
                
                if not found:
                    print("التذكرة غير موجودة")
                    input("\nاضغط Enter...")
                    continue
                
                print(f"\nالتذكرة #{found['id']}")
                print(f"العميل: {found['customer_name']}")
                print(f"الجهاز: {found['device']}")
                print(f"الحالة الحالية: {found['status']}")
                print("\nالحالات:")
                print("1. pending     (قيد الانتظار)")
                print("2. in_progress (تحت الصيانة)")
                print("3. ready       (جاهز)")
                print("4. delivered   (تم التسليم)")
                
                new = input("\nاختر (1-4): ")
                status_map = {'1': 'pending', '2': 'in_progress', '3': 'ready', '4': 'delivered'}
                
                if new in status_map:
                    found['status'] = status_map[new]
                    save_data(data)
                    print(f"\nتم تحديث الحالة")
                else:
                    print("اختيار غير صحيح")
                    
            except:
                print("خطأ")
            
            input("\nاضغط Enter...")
        
        elif choice == '4':
            clear()
            print("--- الْعُمَلَاء ---\n")
            
            if not data['customers']:
                print("لا يوجد عملاء")
            else:
                for c in data['customers']:
                    count = len([t for t in data['tickets'] if t['customer_id'] == c['id']])
                    print(f"👤 {c['name']} | {c['phone']} | {count} تذكرة")
            
            input("\nاضغط Enter...")
        
        elif choice == '5':
            clear()
            total = len(data['tickets'])
            pending = len([t for t in data['tickets'] if t['status'] == 'pending'])
            progress = len([t for t in data['tickets'] if t['status'] == 'in_progress'])
            ready = len([t for t in data['tickets'] if t['status'] == 'ready'])
            delivered = len([t for t in data['tickets'] if t['status'] == 'delivered'])
            
            print("=" * 45)
            print("        الإِحْصَائِيَّات")
            print("=" * 45)
            print(f"إجمالي التذاكر: {total}")
            print(f"قيد الانتظار: {pending}")
            print(f"تحت الصيانة: {progress}")
            print(f"جاهز: {ready}")
            print(f"تم التسليم: {delivered}")
            print(f"عدد العملاء: {len(data['customers'])}")
            print("=" * 45)
            input("\nاضغط Enter...")
        
        elif choice == '6':
            print("\nشكراً لاستخدام النظام")
            break
        
        else:
            print("اختيار غير صحيح")
            input("\nاضغط Enter...")

if __name__ == "__main__":
    main()
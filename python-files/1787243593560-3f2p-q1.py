def star_numbers(number) :
    status = 'NOK'
    for i in range((int(number) // 2) + 1) : # هر عدد را نصف میکنیم(چون که از نظر ریاضی دو عددی که از نصب عدد مورد نظر بزرگتر باشد ضربش خود آن نمیشود به جز اعدای مثل 0 و 1 و -1)
        if i * (i + 1) == int(number) : # خود شماره(که کمتر از نصف عدد اصلی است) را با شماره بعدی ضرب میکنیم
            status = 'OK'
    
    with open('output1.txt' , 'a+') as file : # از حالت ایپند استفاده شده چون که بعد هر نوشتن فایل پاک نشده و تنها در ادامه قبلی باشد(رایت بعد هر باز شدن قبلی را پاک میکندذ)
        file.write(status + '\n')


with open('input1.txt' , 'r') as file :
    file = file.readlines()
    for i in file :
        
        star_numbers(i.strip())


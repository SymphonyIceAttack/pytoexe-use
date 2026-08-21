def star_numbers(number) :
    try :
        status = 'NOK'
        for i in range((int(number) // 2) + 1) : # هر عدد را نصف میکنیم(چون که از نظر ریاضی دو عددی که از نصب عدد مورد نظر بزرگتر باشد ضربش خود آن نمیشود به جز اعدای مثل 0 و 1 و -1)
            if i * (i + 1) == int(number) : # خود شماره(که کمتر از نصف عدد اصلی است) را با شماره بعدی ضرب میکنیم
                status = 'OK'
        return status

    except Exception as error :
        return error



with open('q_1/input1.txt' , 'r') as file_read :
    file_read = file_read.readlines()

    with open('q_1/output1_exe.txt' , 'w') as file_write :
        for i in file_read :
            file_write.write(star_numbers(i.strip()) + '\n')



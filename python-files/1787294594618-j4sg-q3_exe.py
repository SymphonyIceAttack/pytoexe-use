def extraction(data) :
    try :
            moktasat = int(data)
            desimal_minus = (data - moktasat) * 60 #  فقط قسمت اعشار بمونه و ضرب 60 میشه برای ثانیه
            minus = int(desimal_minus)
            desimal_secs = (desimal_minus - minus) * 60
            secs = int(desimal_secs)

            if moktasat % 2 == 0 :
                    return f'{moktasat}|{minus}|{secs}|N' + '\n'
            else :
                    return f'{moktasat}|{minus}|{secs}|S' + '\n'

    except Exception as error :
        return error



with open('q_3/input3.txt' , 'r') as file_read :
    file_read = file_read.readlines()

    with open('q_3/output3_exe.txt' , 'w') as file_write :
        for i in file_read :
            file_write.write(extraction(float(i.strip()))  + '\n')


    
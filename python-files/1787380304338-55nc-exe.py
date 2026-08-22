def numbers_freand(input_file) :
    input_file = input_file.split(' ')
    a = int(input_file[0])
    b = int(input_file[1])

    try :

        def majmoo_maghsoom(number):
            total = 0
            i = 1
            # بررسی جذر
            while i * i <= int(number):
                if number % i == 0:
                    total = total + i
                    if i != number // i:
                        total = total + (number // i)
                i = i + 1
            return total

        # محاسبه مقسوم علیه ها
        sa = majmoo_maghsoom(a)
        sb = majmoo_maghsoom(b)

        # بررسی نسبت 2 تا عدد
        if sa * b == sb * a:
            return 'OK'
        
        else:
            return 'NOK'

    except Exception as error :
        return str(error)


try :

    with open('match_1/q_2/input2.txt' , 'r') as file_read :
        file_read = file_read.readlines()

        with open('match_1/q_2/output2_exe.txt' , 'w') as file_write :
            for i in file_read :
                file_write.write(numbers_freand(i.strip()) + '\n')

except Exception as error :
    print(error)

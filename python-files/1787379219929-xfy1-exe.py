def khodshifte(input_file) :
    try :
        power = len(input_file) 
        total = 0

        for i in input_file:
            total = total + (int(i) ** power)

        if total == int(input_file) :
            return 'OK'

        else :
            return 'NOK'

    except Exception as error :
        return f'error'


try :

    with open('match_1/q_1/input1.txt' , 'r') as file_read :
        file_read = file_read.readlines()

        with open('match_1/q_1/output1_exe.txt' , 'w') as file_write :
            for i in file_read :
                file_write.write(khodshifte(i.strip()) + '\n')

except Exception as error :
    print(error)

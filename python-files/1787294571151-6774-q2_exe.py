import math

def plot_size(number) :
    try :
        return str(int((number ** 2) / (math.pi * 4)))
    except Exception as error :
        return error

with open('q_2/input2.txt' , 'r') as file_read :
    file_read = file_read.readlines()

    with open('q_2/output2_exe.txt' , 'w') as file_write :
        for i in file_read :
            file_write.write(plot_size(int(i.strip())) + '\n')




def orange_count(input_file):
    try:
        number = int(input_file)
        
        total = number * (number + 1) * (number + 2) // 6 # تعداد کل پرتقال‌ها در هرم مثلثی با ضلع 
        
        return str(total)
    
    except Exception as error:
        return str(error)


try:
    with open('q_3/input3.txt', 'r') as file_read:
        file_read = file_read.readlines()
    
    with open('q_3/output3_exe.txt', 'w') as file_write:
        for line in file_read:
                file_write.write(orange_count(line.strip()) + '\n')

except Exception as error:
    print(error)
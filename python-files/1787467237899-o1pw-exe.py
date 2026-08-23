def joft_number(input_file):
    try:
        # خواندن اعداد از ورودی
        parts = input_file.split()
        arr = []
        for p in parts:
            arr.append(int(p))
        
        n = len(arr)
        swaps = 0
        i = 0
        

        while i < n - 1 : #ش آرایه از ابتدا پیمای
            
            if arr[i] == arr[i + 1] : # اگر دو عنصر کنار هم برابر باشند، جفت درست است
                i = i + 2
                continue
            
            # پیدا کردن جفت 
            j = i + 2
            found = False
            while j < n:
                if arr[j] == arr[i] :
                    found = True
                    break
                j = j + 1
            
            if found == True :

                temp = arr[i + 1]
                arr[i + 1] = arr[j]
                arr[j] = temp
                swaps = swaps + 1
            
            
            i = i + 2 # حرکت به جفت بعدی
        
        return str(swaps)
    
    except Exception as error:
        return str(error)


try:
    with open('q_2/input2.txt', 'r') as file_read:
        file_read = file_read.readlines()
    
    with open('q_2/output2_exe.txt', 'w') as file_write:
        for line in file_read:
            file_write.write(joft_number(line.strip()) + '\n')

except Exception as error:
    print(error)
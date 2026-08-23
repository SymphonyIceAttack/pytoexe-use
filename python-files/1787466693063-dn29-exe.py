def sorted_sood(input_file) :
    try:
        parts = input_file.split()
        nums = []
        for x in parts:
            nums.append(int(x))
       
        has_zero = False
        for x in nums:
            if x == 0:
                has_zero = True
                break
       
        if has_zero:
            return "!!!"
       
        pos = []
        neg = []
        for x in nums:
            if x > 0:
                pos.append(x)
            elif x < 0:
                neg.append(x)
       
        if len(neg) == 0:
            res = sorted(pos)
       
        elif len(pos) == 0:
            res = sorted(neg)  # از بیشترین ضرر به کمترین
       
        else:
            pos = sorted(pos, reverse=True)  # سودها از بیشتر به کمتر
            neg = sorted(neg)  #تغییر: ضررها از بیشترین به کمترین
           
            res = []
            i = 0
            j = 0
           
            while i < len(pos) or j < len(neg):
                if i < len(pos):
                    res.append(pos[i])
                    i = i + 1
                if j < len(neg):
                    res.append(neg[j])
                    j = j + 1
       
        out = []
        for x in res:
            out.append(str(x))
       
        return " ".join(out)
   
    except Exception as error:
        return str(error)

try:
    with open('q_1/input_1.txt', 'r') as file_read:
        file_read = file_read.readlines()
   
    with open('q_1/output1_exe.txt', 'w') as file_write:
        for i in file_read:
            file_write.write(sorted_sood(i.strip()) + '\n')
except Exception as error:
    print(error)
mo7asba = float(input("mo7asba : "))
mo7asbatd = float(input("mo7asba td: "))

i9tisad = float(input("i9tisad: "))
i9tisadtd  = float(input("i9tisad td : "))

kanoun = float(input("9anoun : "))

english = float(input("english : "))
englishtd = float(input("english td : "))


french  = float(input("french : "))
frenchtd = float(input("french td : "))

i7timalt = float(input("i7timalat : "))
i7timalttd = float(input("i7timalattd : "))


algebr = float(input("algebr : "))
algebrtd = float(input("algebr td  : "))


analyse = float(input("analyse  : "))
analysetd = float(input("analyse  : "))


oloumijtima3iya = float(input("3ouloum ijtima3iya : "))

info = float(input("info: " ))
infotd = float(input("info td: " ))

mo7asba_sum = ((mo7asba * 0.6)+(mo7asbatd * 0.4)) * 2
i9tisadsum = ((i9tisad * 0.6)+(i9tisadtd * 0.4)) * 2
kanoun_sum = kanoun
i7timalat_sum = ((i7timalt * 0.6)+(i7timalttd*0.4))*2
algebr_sum = ((algebr * 0.6)+ (algebrtd * 0.4))*3
analyse_sum = ((analyse * 0.6 )+ (analysetd * 0.4))*3
english_sum =  ((english * 0.6)+ (englishtd * 0.4))
french_sum = ((french * 0.6)+ (frenchtd * 0.4))
info_sum = ((info * 0.6 ) + (infotd * 0.4)) * 2

sum = (mo7asba_sum + i9tisadsum + kanoun_sum + i7timalat_sum + algebr_sum + analyse_sum + english_sum + french_sum + oloumijtima3iya) / 18
print(sum)

quit = input("press any key")
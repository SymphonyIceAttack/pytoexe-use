def calculate_bmi(weight, height):
    height_m = height / 100
    bmi =weight / (height_m ** 2)
    return round(bmi,2)
def judge_bmi(bmi):
    if bmi < 18.5:
        return "偏瘦"
    elif 18.5 <= bmi < 24:
        return "正常"
    elif 24 <= bmi <28:
        return "超重"
    else:
        return "肥胖"
def main():
    print("=" * 30)
    print("简易bmi计算器")
    print("=" * 30)
    while True:
        print("\n请输入您的信息 (输入q退出)")
        weight_input = input("体重(kg):")
        if weight_input . lower() == 'q':
            print("程序结束")
            break
        
        height_input = input("身高(cm):")
        if height_input . lower() == 'q':
            print("程序结束")
            break
        try:
            weight = float(weight_input)
            height = float(height_input)
            if weight <=0 or height <=0:
                print("身高体重必须为正数，请重新输入。")
                continue
        except ValueError:
            print("输入无效，请输入数字。")
            continue
        bmi = calculate_bmi(weight,height)
        result = judge_bmi(bmi)
        print(f"\n你的bmi指数为:{bmi}")
        print(f"体型状态:{result}")
if __name__ == "__main__":
    main()
Python 3.14.2 (tags/v3.14.2:df79316, Dec  5 2025, 17:18:21) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> import random
... 
... def generate_lotto_numbers():
...     """
...     로또 번호 6개와 보너스 번호 1개를 생성하는 함수
...     1~45 범위에서 중복 없이 번호를 뽑습니다.
...     """
...     try:
...         # 1~45 범위에서 6개 번호 추출
...         main_numbers = random.sample(range(1, 46), 6)
...         main_numbers.sort()  # 오름차순 정렬
... 
...         # 남은 번호 중에서 보너스 번호 1개 추출
...         remaining_numbers = set(range(1, 46)) - set(main_numbers)
...         bonus_number = random.choice(list(remaining_numbers))
... 
...         return main_numbers, bonus_number
...     except Exception as e:
...         print(f"오류 발생: {e}")
...         return [], None
... 
... def main():
...     print("=== 파이썬 로또 번호 생성기 ===")
...     main_nums, bonus = generate_lotto_numbers()
... 
...     if main_nums and bonus:
...         print(f"로또 번호: {main_nums}")
...         print(f"보너스 번호: {bonus}")
...     else:
...         print("번호 생성에 실패했습니다.")
... 
... if __name__ == "__main__":
...     main()

#!/usr/bin/env python
# coding: utf-8

# In[2]:


import requests
from bs4 import BeautifulSoup

def get_dollar_price():
    url = "https://www.tgju.org/profile/price_dollar_rl"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # استخراج قیمت‌ها
        current_rate = soup.find(text="نرخ فعلی").find_next().text.strip()
        highest_rate = soup.find(text="بالاترین قیمت روز").find_next().text.strip()
        lowest_rate = soup.find(text="پایین ترین قیمت روز").find_next().text.strip()
        
        # نمایش قیمت‌ها به صورت زیبا
        print("\n===============================")
        print("          قیمت دلار          ")
        print("===============================\n")
        print(f"نرخ فعلی: {current_rate} تومان")
        print(f"بالاترین قیمت روز: {highest_rate} تومان")
        print(f"پایین ترین قیمت روز: {lowest_rate} تومان")
        print("\n===============================\n")
    else:
        print("خطا در دریافت اطلاعات")

# اجرای تابع
get_dollar_price()

# منتظر ماندن برای خروج (فقط در محیط‌های غیر Jupyter)
# input("برای خروج، Enter را فشار دهید...")


# In[ ]:





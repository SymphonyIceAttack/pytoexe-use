import os
from datetime import datetime
import requests
import json
import time
import datetime
from multiprocessing import Queue
from configparser import ConfigParser
import time
import datetime
from decimal import Decimal
from client import Client
from exceptions import BinanceAPIException, BinanceRequestException, BinanceWithdrawException
import winsound
import json
import csv
import re
import sys
import fileinput
from tempfile import mkstemp
from os import close
from shutil import move
import getmac



##### Подключаем TradingView - Analyze Your Chart ########################
from tradingview_ta import *
import time
import functools
from functools import lru_cache
import requests

from colorama import Fore, Style
from tradingview_ta import TA_Handler, Interval, get_multiple_analysis
import tradingview_ta, requests, argparse
##### Подключаем end TradingView - Analyze Your Chart ########################

l = 0
srednia = 0
R = 0
balances_kupili = 0
balances_kupili_prodaje = 0
kolicPARA = 0

mac = getmac.get_mac_address()
# fjfprint(mac)

while 1 == 1:
    """
    if (str(mac) == '00:0c:29:b0:02:cb') or (str(mac) == '56:b8:ca:00:66:a7') or (str(mac) == '00:00:00:00:00:00') or (str(mac) == 'f0:76:1c:b8:5c:8d'):
        print("ok")
    else:
        break
    """
    f=open('N.txt')
    for line in f:
        with open('N.txt', 'r') as f:
            nums = f.read().splitlines()
        #print(nums)
        try:    
            t = nums[0]
        except Exception:
            time.sleep(30)
            t=0
            break
    print("t",t)
    
    print("#############################################", l ,"#######################################")
    print(" Биржа binance 05-03-2026 vse")
    #print("Versia 4 Зашита от добавление дубликатов")

    ##### Подключаем файл ########################
    client = Client('kT6gCQUfnsmMzyxWv4hoZHAnhuEe0Lbvf3tLRfwzuKek43a4COUhfAOhqU3x9tgB', 'IWSVajYuQWyih1ebKNboihzDBGRNusjo6T3LNsjhQK9WjPwg9NVZ19Q8CRqhO0Sz')
    ### настройки из файла #######################
        
    f=open('G:\\Мой диск\\vse\\test\\3.txt')
    for line in f:
        with open('G:\\Мой диск\\vse\\test\\3.txt', 'r') as f:
            nums = f.read().splitlines()
        print(nums)
        try:
            P = nums[int(t)]
            print("P",P)
        except Exception:
            P=0
            break
            print("P",P)
    try:
        q = P.replace("USDT",'')
    except Exception:
        q=0
        print("PARA",q)
        if int(q) == 0:
            filehandle = open('N.txt', 'w')
            filehandle.write(str(0))
            filehandle.close()
            
            time.sleep(30)
            continue
    
    print("PARA",q)
    
    try:
        kolicPARA = len(q)
    except Exception:
        kolicPARA = 0
    print("kolicPARA",kolicPARA)
    
    filehandle = open('PARA.txt', 'w')
    filehandle.write(str(q))
    filehandle.close()
    h=0
    f=open('PARA.txt')
    with open('PARA.txt', 'r') as f:
        nums = f.read().splitlines()
        #print(nums)
        try:
            P = nums[h]
            print("P1:",P)
        except Exception:
            P = 0
            print("P2:",P)
    try:
        kolicP = len(q)
    except Exception:
        kolicP = 0
    print("kolicP",kolicP)    
    
    ########################## проверка ########################
    
    
    
    PARA = P#cfg['PARA']['para']
    CURRENCY = 'USDT'
    TICKER = '{para}{currency}'.format(para=PARA,currency=CURRENCY)
    PARA2 = '{para}'.format(para=PARA)
    print("Пара:", TICKER)

    #######################################
    
    get_ticker = client.get_ticker ()
    #print("get_ticker:",get_ticker)
    x = 0
    i = 0
    symbol = 0
    volume_ticker = 0
    for x in get_ticker:
        #print(x)
        symbol = get_ticker[i]['symbol']
        volume_ticker = get_ticker[i]['volume']
        priceChangePercent = get_ticker[i]['priceChangePercent']
        lastPrice = get_ticker[i]['lastPrice']
        lowPrice = get_ticker[i]['lowPrice']
        highPrice = get_ticker[i]['highPrice']
        volume_BTC = float(lastPrice) * float(volume_ticker)
        volume_BTC2 = str(round(volume_BTC,5))
        if symbol == TICKER:
            print("#############################################", l ,"#######################################")
            print("ДАННЫЕ О ТОРГОВАЙ ПАРЕ")
            print("")
            print("| Валютная пара  |       Объем          |     Процент     |     Цена    |   Объем в USDT  |")
            print("|",symbol," "*(13-len(symbol)),"|",volume_ticker," "*(14-len(volume_ticker)),"|",priceChangePercent," "*(14-len(priceChangePercent)),"|",lastPrice," "*(10-len(lastPrice)),"|",volume_BTC2," "*(14-len(volume_BTC2)),"|")

            break
        i = i + 1
    #######################################################################
    """
    print("Самая высокая цена",highPrice)
    print("Текушая цена",lastPrice)
    
    f=open('highPrice.txt')
    with open('highPrice.txt', 'r') as f:
        nums = f.read().splitlines()
        #print(nums)
        try:
            high = nums[k]
        except Exception:
            high = 0
            print("high:",high)
        print("Самая высокая цена из файла:",high)
    if (float(highPrice) != float(high)):
        filehandle = open('highPrice.txt', 'w')
        filehandle.write(str(highPrice))
        filehandle.close()
        
    """
    
    if (kolicP == 0) or (kolicP == 1):

        filehandle = open('N.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        time.sleep(30)  
        continue
    
    
    #Отступ первого ордера---------------------------------------

    #otstup_sverhu = cfg['procent-pro2']['p5'] #Проверяим отступ сверху
    #print("Проверяим отступ сверху",otstup_sverhu)

    ord_otstup1 = 0#float(otstup_sverhu)/2 #Отступ первого ордера
    #print("Отступ первого ордера",ord_otstup1)

    ord_otstup2 = 0 
    if float(priceChangePercent) < 20:
        ord_otstup2 = 2
    else:
        ord_otstup2 = float(priceChangePercent)/10
    #ord_otstup2 = 3#cfg['otstup-vtorogo']['p2'] #Отступ остальных ордеров
    print("Отступ остальных ордеров",ord_otstup2)


    btc_total = 15#cfg['kolicbtc']['kb']# Сколько денег будет в каждом ордере
    #print("Сколько денег будет в каждом ордере",btc_total)

    btc_ord = 2 
    btc_ord_2 = 3#cfg['kolicord2']['ko'] #Количество ордеров
    #print("Количество ордеров",btc_ord_2)

    btc_proc_uvilic = 1.1 #cfg['procent-uv-kajda-orde']['h'] #Прочент увелечение сумму каждого ордера
    #print("Прочент увелечение сумму каждого ордера",btc_proc_uvilic)

    procen_prodaji = 0 
    if float(priceChangePercent) < 10:
        procen_prodaji = 1
    else:
        procen_prodaji = float(priceChangePercent)/10
    #procen_prodaji = cfg['procent-pro']['p4'] # Прочент продажи
    print("Прочент продажи",procen_prodaji)

    interval_info = 180#cfg['interval-info']['f']
    #print("Время обнавление:", interval_info)

    interval_info2 = 1#cfg['interval-info2']['f2']

    poslednii_order = 0#cfg['poslednii']['poslednii_order']
    #print("Последнии ордер", poslednii_order)

    signal = 19#cfg['signal']['s']

    #R = cfg['vremea']['v']
    ### настройки из файла #######################


    
    #############################################################
    x = 0 
    i = 0
    order = client.get_account()['balances']
    #print(order)
    for x in order:
        #print(x)
        asset = order[i]['asset']
        #print(asset)
        if asset == CURRENCY:
            balances_vse = order[i]
            #print(balances_vse)
            balances = order[i]['free']
            #print("Баланс BTC",balances)
            break
        i = i + 1
    x = 0 
    i = 0
    for x in order:
        #print(x)
        asset = order[i]['asset']
        #print(asset)
        if asset == PARA:
            balances_vse = order[i]
            #print(balances_vse)
            balances_kupili2 = order[i]['free']
            balances_kupili = Decimal('{:.4f}'.format(Decimal(balances_kupili2)))
            print("Сколько на балансе:",balances_kupili)
            balances_kupili_prodaje = order[i]['locked']
            print("Сколько поставлено на продажу:",balances_kupili_prodaje)
            break
        i = i + 1

    TradeHistory = 0
    TradeHistory2 = 0
    try:
        TradeHistory = client.get_my_trades(symbol=TICKER)
        TradeHistory2 = TradeHistory
        #print(TradeHistory2)
    except Exception:
        time.sleep(int(interval_info2))
        #print("Ошибка истории")
        time.sleep(5)
        continue
    
    open_orders = 0
    open_orders2 = 0
    try:
        open_orders = client.get_open_orders(symbol=TICKER)
        open_orders2 = open_orders
        #print(open_orders2)
    except Exception:
        time.sleep(int(interval_info2))
        #print("Ошибка ордера")

    my_spisok = 0
    kolic = 0
    try:
        my_spisok = open_orders2
        print(my_spisok)
        kolic = len(my_spisok)
        print ("Количества ордеров открытых:", kolic)
    except Exception:
        kolic = 1
        #print("Ошибка Количества ордеров открытых")

    my_spisok2 = 0
    kolicHistory = 0
    try:
        my_spisok2 = TradeHistory2
        #print(my_spisok)
        kolicHistory = len(my_spisok2)
        #print ("Количества ордеров в истории:", kolicHistory)
    except Exception:
        kolicHistory = 1
        print("")
    ###########################################################
    
    #Читаем из файла
    k=0
    a = 0
    try:
        f=open('G:\\Мой диск\\vse\\test\\3.txt')
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\3.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
    try:
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            R = nums[k]
            print("Время интервала графика:",R)
    except Exception:
        filehandle = open('Interval\\'+PARA+'Interval.txt', 'w')
        filehandle.write(str(5))
        filehandle.close()
    #Читаем из файла конец
    ###########################################################    
    ##### Подключаем TradingView - Analyze Your Chart ########################
    if int(R) == 1:
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_1_MINUTE,
            screener="crypto",
            exchange="binance"
        )
        print ("Интервал:", R)
    elif int(R) == 5 :
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_5_MINUTES,
            screener="crypto",
            exchange="binance"
        )
        print ("Интервал:", R)
    elif int(R) == 15 :
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_15_MINUTES,
            screener="crypto",
            exchange="binance"
        )
        print ("Интервал:", R)
    elif int(R) == 30 :
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_30_MINUTES,
            screener="crypto",
            exchange="binance"
        )
        print ("Интервал:", R)
    elif int(R) == 60 :
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_1_HOUR,
            screener="crypto",
            exchange="binance"
        )
        
        print ("Интервал:", R)
    elif int(R) == 240 :
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_4_HOURS,
            screener="crypto",
            exchange="binance"
        )
        print ("Интервал:", R)
    elif int(R) == 24 :
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_1_DAY,
            screener="crypto",
            exchange="binance"
        )
        print ("Интервал:", R)
    else:
        handler = TA_Handler(
            symbol=TICKER,
            interval=Interval.INTERVAL_5_MINUTES,
            screener="crypto",
            exchange="binance"
        )
    data_tuple = handler.get_analysis().indicators
    #print(data_tuple)

    @lru_cache(maxsize=128)
    def process_data(data_tuple): # Принимает кортеж
        #print(f"Processing data: {data_tuple}")
        # Имитация дорогой операции
        return data_tuple
        
    result1 = process_data(tuple(data_tuple))
    for item in result1:
        """
        #print(f"Result 1: {item}:{data_tuple[item]}")
        print(f"EMA50: {data_tuple['EMA50']}")
        print(f"EMA100: {data_tuple['EMA100']}")
        print(f"EMA200: {data_tuple['EMA200']}")
        print(f"ADX: {data_tuple['ADX']}")
        print(f"ADX+DI: {data_tuple['ADX+DI']}")
        print(f"ADX-DI: {data_tuple['ADX-DI']}")
        print(f"ADX+DI[1]: {data_tuple['ADX+DI[1]']}")
        print(f"ADX-DI[1]: {data_tuple['ADX-DI[1]']}")
        print(f"MACD.macd: {data_tuple['MACD.macd']}")
        print(f"MACD.signal: {data_tuple['MACD.signal']}")
        print(f"RSI: {data_tuple['RSI']}")
        print(f"RSI[1]: {data_tuple['RSI[1]']}")
        print(f"low: {item}:{data_tuple['low']}")
        """
        #print(f"Result 2: {data_tuple[item]}")
        #time.sleep(60)
    """    
    print("#########################################################")
    print(f"ADX: {data_tuple['ADX']}")
    print(f"ADX+DI: {data_tuple['ADX+DI']}")
    print(f"ADX-DI: {data_tuple['ADX-DI']}")
    print(f"ADX+DI[1]: {data_tuple['ADX+DI[1]']}")
    print(f"ADX-DI[1]: {data_tuple['ADX-DI[1]']}")
    print(f"EMA100: {data_tuple['EMA100']}")
    print(f"EMA200: {data_tuple['EMA200']}")
    print(f"RSI: {data_tuple['RSI']}")
    print(f"RSI[1]: {data_tuple['RSI[1]']}")
    print(f"CCI20: {data_tuple['CCI20']}")
    print(f"CCI20[1]: {data_tuple['CCI20[1]']}")
    print(f"W.R: {data_tuple['W.R']}")
    print(f"volume: {data_tuple['volume']}")
    #print(f"high: {data_tuple['high']}")
    #print(f"low: {data_tuple['low']}")  
    #print(handler.get_analysis().summary)
    print("#########################################################")
    """
    #print(f"EMA50: {data_tuple['EMA50']}")
    #print(f"EMA100: {data_tuple['EMA100']}")
    #print(f"EMA200: {data_tuple['EMA200']}")
    volume_ = data_tuple['volume']
    AO = data_tuple['AO']
    CCI20 = data_tuple['CCI20']
    WR = data_tuple['W.R']
    RSI = data_tuple['RSI']
    EMA50 = data_tuple['EMA50']
    EMA100 = data_tuple['EMA100']
    if int(R) == 1:
        EMA200 = data_tuple['EMA50']
    elif int(R) == 5:
        EMA200 = data_tuple['EMA100']
    elif int(R) == 15:
        EMA200 = data_tuple['EMA100']
    elif int(R) == 30:
        EMA200 = data_tuple['EMA100']
    elif int(R) == 60:
        EMA200 = data_tuple['EMA100']
    elif int(R) == 24:
        EMA200 = data_tuple['EMA100']
    else:
        pass
    low = data_tuple['low']
    high = data_tuple['high']
    pervii_order = high
    ADX_DI = data_tuple['ADX+DI']
    ADX_DI2 = data_tuple['ADX-DI']
    ADX_SUMA = (float(ADX_DI2)-float(ADX_DI))
    ADX_SUMA2 = abs(ADX_SUMA)
    P_SAR = data_tuple['P.SAR']
    BB_lower = data_tuple['BB.lower']
    RecommendAll = data_tuple['Recommend.All']
    RecommendMA = data_tuple['Recommend.MA']
    AO = data_tuple['AO']
    """
    print("AO:",AO)
    print("WR:",WR)
    print("RSI:",RSI)
    print("low:",low)
    #print("EMA100:",EMA100)
    print("EMA200:",EMA200)
    print("ADX_SUMA:",abs(ADX_SUMA),abs(ADX_SUMA2))
    """
    #print("P.SAR:",P_SAR)
    #print("BB.lower:",BB_lower)
    
    #print("low:",low)
    #print("EMA200:",EMA200)
    
    #print("Recommend.All:",RecommendAll)
    #print("Recommend.MA:",RecommendMA)
    #print("AO:",AO)
    
    #Удаляем файл после всех условии
    
    #Удаляем файл после всех условии end
    
    #Записываем в файл volume symbol
    """
    filehandle = open('4.txt', 'a')
    filehandle.write("-----------------------------------------------------------" + '\n')
    filehandle.write("symbol:" + str(symbol) + " " +"Interval:" + str(R) + " " + "volume:"+volume + " "+ "%" + priceChangePercent + '\n')
    filehandle.write("ADX_SUMA2:" + str(ADX_SUMA2) + " " + "AO:" + str(AO) + " " + "WR:" + str(WR) + " " + "RSI:" + str(RSI) + '\n')
    filehandle.write(str(data_tuple) + '\n')  
    #filehandle.write(symbol)  
    filehandle.close()
    #Записываем в файл конец
    
    #Записываем в файл ADX
    filehandle = open('ADX\\ADX'+R+PARA+'.txt', 'a')
    filehandle.write("Interval:" + str(R) + '\n') 
    filehandle.write("symbol:" + str(symbol) + " " +"Interval:" + str(R) + " " + "volume:"+volume_ticker + " "+ "%" + priceChangePercent + '\n')
    filehandle.write("ADX_DI+:" + str(ADX_DI) + " " + "ADX_DI-:" + str(ADX_DI2) + '\n')
    filehandle.write("ADX_SUMA:" + str(ADX_SUMA2) + '\n') 
    filehandle.write("P.SAR:" + str(P_SAR) + '\n')
    filehandle.write("BB.lower:" + str(BB_lower) + '\n')
    filehandle.write("Recommend.All:" + str(RecommendAll) + '\n')
    filehandle.write("Recommend.MA:" + str(RecommendMA) + '\n')
    filehandle.write("AO:" + str(AO) + '\n')
    filehandle.write("RSI:" + str(RSI) + str(data_tuple) + '\n')
    filehandle.write("R:" + str(R) + '\n')
    filehandle.close()
    #Записываем в файл конец
    """
#######################ADX_DI+ Ишим максимум и минимум ############################################ 
    print("ADX_SUMA:",abs(ADX_SUMA2))
    
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_SUMAmax = nums[k]
            print("ADX_SUMAmax:",ADX_SUMAmax)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
    try:
        if float(ADX_SUMA2) > float(ADX_SUMAmax):
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt', 'w')
            filehandle.write(str(ADX_SUMA2))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(ADX_SUMA2))
        filehandle.close()
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DImax.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_SUMAmax.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_SUMAmax5 = nums[k]
            print("ADX_SUMAmax5:",ADX_SUMAmax5)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
   #Читаем из файла конец




    print("ADX_DI+:",ADX_DI)  
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_DImax = nums[k]
            print("ADX_DI+max:",ADX_DImax)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt', 'w')
        filehandle.write(str(ADX_DI))
        filehandle.close()
   #Читаем из файла конец
    try:
        if float(ADX_DI) > float(ADX_DImax):
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt', 'w')
            filehandle.write(str(ADX_DI))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt', 'w')
        filehandle.write(str(ADX_DI))
        filehandle.close()
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DImax.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DImax.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_DImax5 = nums[k]
            print("ADX_DI+max5:",ADX_DImax5)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DImax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
    #Записываем в файл ADX_DI конец max
    
    
    #Записываем в файл ADX_DI min
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+R+'ADX_DImin.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_DImin = nums[k]
            #print("ADX_DI+min:",ADX_DImin)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt', 'w')
        filehandle.write(str(ADX_DI))
        filehandle.close()
    #Читаем из файла конец
    try:
        if float(ADX_DI) < float(ADX_DImin):
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt', 'w')
            filehandle.write(str(ADX_DI))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt', 'w')
        filehandle.write(str(ADX_DI))
        filehandle.close()
    #Записываем в файл ADX_DI+ конец max
    
    #Читаем из файла min1
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                ADX_DImin_1 = nums[k]
                #print("ADX_DI+min:",ADX_DImin)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImin.txt', 'w')
        filehandle.write(str(ADX_DI))
        filehandle.close()
    #Читаем из файла конец 1
    
########################ADX_DI+ Ишим максимум и минимум конец ###########################################    
  
   
#######################ADX_DI- Ишим максимум и минимум ############################################ 
    
    print("ADX_DI-:",ADX_DI2)  
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_DI2max = nums[k]
            print("ADX_DI-max:",ADX_DI2max)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'w')
        filehandle.write(str(ADX_DI2))
        filehandle.close()
        ADX_DI2max = 0
   #Читаем из файла конец
    try:
        if float(ADX_DI2) > float(ADX_DI2max):
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'w')
            filehandle.write(str(ADX_DI2))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'w')
        filehandle.write(str(ADX_DI2))
        filehandle.close()
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DI2max.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DI2max.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_DI2max5 = nums[k]
            print("ADX_DI-max5:",ADX_DI2max5)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+'5ADX_DI2max.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
    #Записываем в файл ADX_DI- конец max
    
    #Записываем в файл ADX_DI- min
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            ADX_DI2min = nums[k]
            #print("ADX_DI-min:",ADX_DI2min)
    
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt', 'w')
        filehandle.write(str(ADX_DI2))
        filehandle.close() 
        #Читаем из файла конец
        ADX_DI2min = 0
    try:
        if float(ADX_DI2) < float(ADX_DI2min):
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt', 'w')
            filehandle.write(str(ADX_DI2))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt', 'w')
        filehandle.write(str(ADX_DI2))
        filehandle.close()
    #Записываем в файл ADX_DI- конец max
    
    #Читаем из файла max1
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                ADX_DI2max = nums[k]
                print("ADX_DI-max:",ADX_DI2max)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'w')
        filehandle.write(str(ADX_DI2))
        filehandle.close()
        ADX_DI2max_1 = 0
    #Читаем из файла конец
    #Читаем из файла min
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                ADX_DI2min_1 = nums[k]
                print("ADX_DI-min:",ADX_DI2min)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2min.txt', 'w')
        filehandle.write(str(ADX_DI2))
        filehandle.close()
        ADX_DI2min_1 = 0
    #Читаем из файла конец 1
    
    
########################ADX_DI- Ишим максимум и минимум конец ###########################################    
   
    
 
########################CCI20 Ишим максимум и минимум ############################################ 
    print("CCI20:",CCI20)   
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20max.txt') 
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20max.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            CCI20max = nums[k]
            print("CCI20max:",CCI20max)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20max.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
   #Читаем из файла конец
    try:
        if float(CCI20) > float(CCI20max):
            filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20max.txt', 'w')
            filehandle.write(str(CCI20))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20max.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
    
    #Записываем в файл CCI20 конец max
    
    #Записываем в файл CCI20 min
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20min.txt')
     
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20min.txt', 'r') as f:
                nums = f.read().splitlines()
            #print(nums)
            CCI20min = nums[k]
            print("CCI20min:",CCI20min)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20min.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
    #Читаем из файла конец
    try:
        if float(CCI20) < float(CCI20min):
            filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20min.txt', 'w')
            filehandle.write(str(CCI20))
            filehandle.close()  
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+str(R)+'CCI20min.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
    #Записываем в файл CCI20 конец max
     
    #Читаем из файла max
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\CCI20\\CCI20max1.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20max1.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                CCI20max_1 = nums[k]
                print("CCI20max1:",CCI20max_1)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20max1.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
        CCI20max_1 = 0
    #Читаем из файла конец
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20max5.txt')
        for line in f:
            with open('CCI20max5.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                CCI20max_5 = nums[k]
                #print("CCI20max5:",CCI20max_5)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20max5.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
        CCI20max_5 = 0
    #Читаем из файла конец
    
    #Читаем из файла min
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20min1.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20min1.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                CCI20min_1 = nums[k]
                #print("CCI20min1:",CCI20min_1)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20min1.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
        CCI20min_1 = 0
    #Читаем из файла конец
    #Читаем из файла
    k=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20min5.txt')
        for line in f:
            with open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20min5.txt', 'r') as f:
                nums = f.read().splitlines()
                #print(nums)
                CCI20min_5 = nums[k]
                #print("CCI20min5:",CCI20min_5)
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\CCI20\\'+PARA+'CCI20min5.txt', 'w')
        filehandle.write(str(1))
        filehandle.close()
        CCI20min_5 = 0
    #Читаем из файла конец
########################CCI20 Ишим максимум и минимум конец ###########################################    
    if ((int(R) == 15) and (float(ADX_SUMAmax5) < 30) and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2)) or ((float(volume_ticker) < 4000000) and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2)):
        f=open('G:\\Мой диск\\vse\\test\\3.txt', 'r' , encoding='utf-8' )
        with open('G:\\Мой диск\\vse\\test\\3.txt', 'r') as f:
            nums = f.read().splitlines()
            #print(nums)
            PARAK = nums[int(t)]
        print("PARAK:",PARAK)

        with open('G:\\Мой диск\\vse\\test\\3.txt', 'r', encoding='utf-8') as file:
            content = file.read() # Читаем весь файл
            
        # Удаляем слово 'bad_word'
        new_content = content.replace(str(PARAK), '') # Заменяем на пустую строку

        with open('G:\\Мой диск\\vse\\test\\3.txt', 'w', encoding='utf-8') as file:
            file.write(new_content) # Записываем измененное содержимое

        filehandle = open('G:\\Мой диск\\vse\\test\\1.txt', 'a')  
        filehandle.write(PARAK + '\n')   
        filehandle.close()
        #Удаляем файл после всех условии end
        ORIGINAL = "G:\\Мой диск\\vse\\test\\3.txt"
        EDITED   = "G:\\Мой диск\\vse\\test\\33.txt"

        with open(ORIGINAL) as orig, open(EDITED, "w") as edited:
            for line in orig:
                if line.strip():
                    edited.write(line)
                    
        input_file = 'G:\\Мой диск\\vse\\test\\33.txt'
        output_file = 'G:\\Мой диск\\vse\\test\\3.txt'

        try:
            # Открываем оба файла с помощью менеджера контекста
            with open(input_file, 'r', encoding='utf-8') as source_f:
                with open(output_file, 'w', encoding='utf-8') as dest_f:
                    # Перебираем строки в исходном файле
                    for line in source_f:
                        # Записываем каждую строку в целевой файл
                        dest_f.write(line)
            print(f"Строки успешно скопированы из {input_file} в {output_file}")
        except FileNotFoundError:
            print(f"Ошибка: Файл {input_file} не найден.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+R+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(5)) 
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+R+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+R+'ADX_DImax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+R+'ADX_DI2max.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        break
    
    
    
    if (int(R) == 5) and (float(ADX_SUMA2) > 30) and (float(volume_ticker) > 10000000) and (float(RSI) > 65) and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
        try:
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\ADX_SUMAmax'+str(R)+PARA+'.txt', 'w')
            filehandle.write(str(0))
            filehandle.close()
        except Exception:
            filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\ADX_SUMAmax'+str(R)+PARA+'.txt', 'w')
            filehandle.write(str(0))
            filehandle.close()
        #Записываем в файл 
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(1)) 
        #filehandle.write(symbol)  
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+R+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
    #Записываем в файл Interva
    if (int(R) == 1) and (float(ADX_DI) < float(ADX_DI2)):
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\ADX_SUMAmax'+str(R)+PARA+'.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        #Записываем в файл 
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(5)) 
        #filehandle.write(symbol)  
        filehandle.close()
        #Записываем в файл конец
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
    elif (int(R) == 5) and (float(ADX_DI) < float(ADX_DI2)):
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\ADX_SUMAmax'+str(R)+PARA+'.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        #Записываем в файл 
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(15)) 
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
        #filehandle.write(symbol) 
    elif (int(R) == 15) and (float(ADX_DI) < float(ADX_DI2)):
        #Записываем в файл 
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(30)) 
        filehandle.close()
        #filehandle.write(symbol) 
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
    elif (int(R) == 30) and (float(ADX_DI) < float(ADX_DI2)):
        #Записываем в файл 
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(60)) 
        filehandle.close()
        #filehandle.write(symbol) 
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
    else:
        pass

    #Записываем в файл Interval конец  
    #################################количество нулей после точки
    currentPrice = 0
    currentPrice = low#client.get_order_book(symbol=TICKER)['bids'][0][0]
    #print("currentPrice",currentPrice)
    def count_decimal_places_decimal(number):
        # Преобразуем в Decimal и затем в строку для подсчета знаков
        # Хотя мы и преобразуем в строку, само число обрабатывается в decimal
        # Чтобы получить длину дробной части:
        d = Decimal(str(number)) # Важно сначала в строку, чтобы сохранить точность
        # Убираем целую часть (если есть) и считаем длину
        if '.' in str(d):
            return len(str(d).split('.')[-1])
        return 0
    #h = 0.0000245
    # Пример:
    #print(count_decimal_places_decimal(currentPrice))  # Вывод
    s = count_decimal_places_decimal(currentPrice)
    #print("s:",s)
    j = "{:."
    k = "f}"
    cena_round_colicestvo = (f"{j}{s}{k}")
    #print(cena_round_colicestvo)
    cena_round2 = Decimal(str(cena_round_colicestvo).format(Decimal(currentPrice)))
    #print(cena_round2)
    
    #################################количество нулей после точки конец
    #Записываем в файл Interval

    #########################################################################################
    
    if float(balances_kupili) > 2 :
        ###### start sell #########################################
        print ("ЗАПУСК ПРОГРАММЫ ПРОДАЖИ")
        currentPrice = 0
        currentPrice = client.get_order_book(symbol=TICKER)['bids'][0][0]
        #print("currentPrice",currentPrice)
        print(balances_kupili)
        x = 0
        i = 0
        try:
            for x in open_orders2:
                user_open_orders_order_id = open_orders2[i]['orderId']
                user_open_orders_type = open_orders2[i]['side']
                #print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                
                if user_open_orders_type == "SELL":
                    #print ("Удаляем ордер:", user_open_orders_order_id)
                    order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                    #print(order_cancel)
                i = i + 1
                #print("i=",i)
        except Exception:
            print("Ошибка удаление ордера")

        #print("Баланс после удаление ордера:", balances_kupili)
        if float(balances_kupili_prodaje) != 0:
            time.sleep(5)
            continue
        i = -1
        RTHistory = 0
        RTHistoryvol = 0
        volume = 0
        volume2 = 0
        srednia = 0
        RTHistoryvol_suma = 0
        RTHistoryvol_o = 0
        ordN = 0
        #Запрашиваем историю ордеров
        x = 0
        for x in TradeHistory2:
            ordN = TradeHistory2[i]['commissionAsset']
            #print ("Проверяем если есть BTC:", ordN)
            if float(balances_kupili) > float(RTHistoryvol_suma):
                if ordN == PARA or ordN == 'BNB':
                    RTHistory = TradeHistory2[i]['price'] #Запрашиваем цену купленого ордера
                    #print("RTHistory",RTHistory)
                    RTHistoryvol = TradeHistory2[i]['qty'] #Запрашиваем количества купленого ордера
                    #print ("Запрашиваем количества битковина купленого ордера:", RTHistoryvol)
                    volume = volume + (float(RTHistory)*float(RTHistoryvol))
                    #print ("volume", volume)
                    volume2 = volume2 + float(RTHistoryvol)
                    #print ("volume2", volume2)
                    srednia = volume / volume2

                    RTHistoryvol_suma = float(RTHistoryvol_suma) + float(RTHistoryvol)
                    #print ("Запрашиваем сумму количества битковина купленого ордера:", RTHistoryvol_suma)   
                else:
                    print("ПРОПУСКАЕМ")
            else:
                print("")
                break
            i = i - 1
            print("i=",i)

        #print ("Средния цена", srednia)
        ###################################################
        RTHistoryvol_o = TradeHistory2[-1]['price']
        #print ("Средния цена из истории", RTHistoryvol_o)
        if float(srednia) < float(RTHistoryvol_o):
            srednia = RTHistoryvol_o
            #print ("Средния цена новая", srednia)
        ###################################################
        proc = 0
        print("Процент продажи в параметрах:",procen_prodaji)
        proc = float(srednia)/100*float(procen_prodaji)
        #print("процент ",proc)
        orderprod = 0
        orderprod = float(srednia) + float(proc)
        print("Цена на продажу ",Decimal('{:.4f}'.format(Decimal(orderprod))))
        cena_round = Decimal(str(cena_round_colicestvo).format(Decimal(orderprod)))
        print("cena_round:", cena_round)
        #print("balances_kupili",balances_kupili)
        #-------------------------------
        if float(RTHistoryvol_suma) >= float(balances_kupili):
            ordN_sell_1 = "BUY"
            ordN_sell_2 = PARA
            o = 0
            while int(o) < 20:
                try:
                    ordN_sell_1 = client.get_open_orders(symbol=TICKER)[-1]["side"]
                    ordN_sell_2 = client.get_my_trades(symbol=TICKER)[-1]['commissionAsset']
                    #print(ordN_sell_1)
                    #print(ordN_sell_2)
                except Exception:
                    print("Ошибка 2")
                print("balances_kupili1",balances_kupili)
                try:
                    ordersell = client.order_limit_sell(symbol=TICKER, quantity=balances_kupili, price=cena_round) #cena_round
                    print ("Ставим на продажу:", ordersell)
                except Exception:
                    if ordN_sell_1 == "BUY" and (ordN_sell_2 == "BNB" or ordN_sell_2 == PARA2):
                        if 0.00000001 < float(currentPrice) < 1 :
                            balances_kupili = Decimal('{:.1f}'.format(float(balances_kupili)- 0.1))
                        elif 1 < float(currentPrice) < 3 :
                            balances_kupili = Decimal('{:.2f}'.format(float(balances_kupili)- 0.01))
                        elif 3 < float(currentPrice) < 600 :
                            balances_kupili = Decimal('{:.3f}'.format(float(balances_kupili)- 0.001))
                        else:
                            pass
                        #print("balances_kupili2",balances_kupili)
                        time.sleep(1)
                    else:
                        break
                o = o + 1
                print("o",o)
            time.sleep(5)
            continue    
        else:
            time.sleep(int(interval_info2))
            time.sleep(5)
            continue
    else:
        print(" ")
    ###### end sell ######################################### 
    
    print("ADX+:",abs(ADX_DI))
    print("ADX-:",abs(ADX_DI2))
    print("ADX_SUMA:",abs(ADX_SUMA),abs(ADX_SUMA2))
    print(f"RSI: {data_tuple['RSI']}")
    #print("Volume:",volume_)
    
    ############################################
    try:
        RTHistory = TradeHistory2[-1]['commissionAsset']
    except Exception:
        RTHistory = PARA
    #print("RTHistory",RTHistory)
    #print("lastPrice",lastPrice)
    #print("EMA50",EMA50)
    s=0
    try:
        f=open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'r' , encoding='utf-8' )
    except Exception:
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'a')  
        filehandle.write('')   
        filehandle.close()
    with open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'r') as f:
        nums = f.read().splitlines()
        print(nums)
        try:
            S_B = nums[s]
        except Exception:
            S_B = 0
    print("sellbuy:",S_B)
    
    with open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'r') as file:
        line_count = sum(1 for line in file)
    print("line_count",line_count)
    
    if (RTHistory == "USDT") and (float(line_count) < 2) and ((float(balances_kupili) < 2) or (float(balances_kupili_prodaje) < 2)):
        print("")
    if (RTHistory == "USDT") and (S_B == PARA) and (int(kolic) == 0) and (float(line_count) < 2):
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'a')  
        filehandle.write(RTHistory + '\n')   
        filehandle.close()
    if (RTHistory == PARA) and (S_B != PARA) and (float(line_count) < 2):
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'a')  
        filehandle.write(RTHistory + '\n')   
        filehandle.close()   
    o=0
    f=open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'r' , encoding='utf-8' )
    with open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'r') as f:
        nums = f.read().splitlines()
        print(nums)
        try:
            S_B_Suma = nums[o]
        except Exception:
            S_B_Suma = 0
    print("G:\\Мой диск\\vse\\test\\sellbuy:",S_B_Suma)
    
    with open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'r') as file:
        line_count = sum(1 for line in file)
    print("line_count",line_count)
    #Удаляем файл после всех условии
    
    if (float(R)== 1) and (float(line_count) == 2) and (RTHistory == "USDT") and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
            
        
        #Записываем в файл 
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(5)) 
        #filehandle.write(symbol)  
        filehandle.close()
        #Записываем в файл конец
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'a')  
        filehandle.write('')   
        filehandle.close()
        #Записываем в файл конец
    else:
        pass
    
    if (float(R)== 5 or float(R)== 15 or float(R)== 30 or float(R)== 60) and (int(kolic) == 0) and (float(line_count) == 2) and (RTHistory == "USDT") and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2): 
        f=open('G:\\Мой диск\\vse\\test\\3.txt', 'r' , encoding='utf-8' )
        with open('G:\\Мой диск\\vse\\test\\3.txt', 'r') as f:
            nums = f.read().splitlines()
            #print(nums)
            PARAK = nums[int(t)]
        print("PARAK:",PARAK)
        ###########################################################
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(5)+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        f=open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(5)+'ADX_SUMAmax.txt', 'r' , encoding='utf-8' )
        with open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(5)+'ADX_SUMAmax.txt', 'r') as f:
            nums = f.read().splitlines()
            #print(nums)
            ADX_SUMAmax = nums[int(0)]
        print("PARAK:",ADX_SUMAmax)
        if float(ADX_SUMAmax)!= 0:
            time.sleep(5)
            continue
        ###############################################
        with open('G:\\Мой диск\\vse\\test\\3.txt', 'r', encoding='utf-8') as file:
            content = file.read() # Читаем весь файл
            
        # Удаляем слово 'bad_word'
        new_content = content.replace(str(PARAK), '') # Заменяем на пустую строку

        with open('G:\\Мой диск\\vse\\test\\3.txt', 'w', encoding='utf-8') as file:
            file.write(new_content) # Записываем измененное содержимое

        filehandle = open('G:\\Мой диск\\vse\\test\\1.txt', 'a')  
        filehandle.write(PARAK + '\n')   
        filehandle.close()
    #Удаляем файл после всех условии end
        ORIGINAL = "G:\\Мой диск\\vse\\test\\3.txt"
        EDITED   = "G:\\Мой диск\\vse\\test\\33.txt"

        with open(ORIGINAL) as orig, open(EDITED, "w") as edited:
            for line in orig:
                if line.strip():
                    edited.write(line)
                    
        input_file = 'G:\\Мой диск\\vse\\test\\33.txt'
        output_file = 'G:\\Мой диск\\vse\\test\\3.txt'

        try:
            # Открываем оба файла с помощью менеджера контекста
            with open(input_file, 'r', encoding='utf-8') as source_f:
                with open(output_file, 'w', encoding='utf-8') as dest_f:
                    # Перебираем строки в исходном файле
                    for line in source_f:
                        # Записываем каждую строку в целевой файл
                        dest_f.write(line)
            print(f"Строки успешно скопированы из {input_file} в {output_file}")
        except FileNotFoundError:
            print(f"Ошибка: Файл {input_file} не найден.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        
        filehandle = open('G:\\Мой диск\\vse\\test\\sellbuy\\'+PARA+str(R)+'sellbuy.txt', 'w')  
        filehandle.write('')   
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\Interval\\'+PARA+'Interval.txt', 'w')  
        filehandle.write(str(5)) 
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'PARA+str(R)+'ADX_SUMAmax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DImax.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        filehandle = open('G:\\Мой диск\\vse\\test\\ADX\\'+PARA+str(R)+'ADX_DI2max.txt', 'w')
        filehandle.write(str(0))
        filehandle.close()
        
        continue

    
    print("Сколько на балансе:",balances_kupili)
    print("Сколько поставлено на продажу:",balances_kupili_prodaje)
    print("vse","Интервал:", R,PARA,volume_ticker)
    if (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
        if (float(RSI) > 50) :
            print("float(RSI) > 50:",RSI)
            if int(t) <11:
                t = int(t) + 1
            else:
                t=0
            print("t",t)
            x = 0
            i = 0
            for x in open_orders2:
                user_open_orders_order_id = open_orders2[i]['orderId']
                user_open_orders_type = open_orders2[i]['side']
                print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                            
                if user_open_orders_type == "BUY":
                    print ("Удаляем ордер:", user_open_orders_order_id)
                    order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                    print(order_cancel)
                i = i + 1
                print("i=",i)
            filehandle = open('N.txt', 'w')
            filehandle.write(str(t))
            filehandle.close()
            time.sleep(int(40))
            continue
        elif (float(ADX_SUMA2)>7) and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
            print("float(ADX_SUMA2)>7:",ADX_SUMA2)
            if int(t) <11:
                t = int(t) + 1
            else:
                t=0
            print("t",t)
            x = 0
            i = 0
            for x in open_orders2:
                user_open_orders_order_id = open_orders2[i]['orderId']
                user_open_orders_type = open_orders2[i]['side']
                print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                            
                if user_open_orders_type == "BUY":
                    print ("Удаляем ордер:", user_open_orders_order_id)
                    order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                    print(order_cancel)
                i = i + 1
                print("i=",i)
            filehandle = open('N.txt', 'w')
            filehandle.write(str(t))
            filehandle.close()
            time.sleep(int(40))
            continue
        elif (float(CCI20) < -200) and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
            print("float(CCI20) < -200:",CCI20)
            if int(t) <11:
                t = int(t) + 1
            else:
                t=0
            print("t",t)
            x = 0
            i = 0
            for x in open_orders2:
                user_open_orders_order_id = open_orders2[i]['orderId']
                user_open_orders_type = open_orders2[i]['side']
                print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                            
                if user_open_orders_type == "BUY":
                    print ("Удаляем ордер:", user_open_orders_order_id)
                    order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                    print(order_cancel)
                i = i + 1
                print("i=",i)
            filehandle = open('N.txt', 'w')
            filehandle.write(str(t))
            filehandle.close()
            time.sleep(int(40))
            continue
        elif (float(ADX_SUMAmax5) < 30) and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
            print("ADX_SUMAmax5) < 30:",ADX_SUMAmax5)
            if int(t) <11:
                t = int(t) + 1
            else:
                t=0
            print("t",t)
            x = 0
            i = 0
            for x in open_orders2:
                user_open_orders_order_id = open_orders2[i]['orderId']
                user_open_orders_type = open_orders2[i]['side']
                print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                            
                if user_open_orders_type == "BUY":
                    print ("Удаляем ордер:", user_open_orders_order_id)
                    order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                    print(order_cancel)
                i = i + 1
                print("i=",i)
            filehandle = open('N.txt', 'w')
            filehandle.write(str(t))
            filehandle.close()
            time.sleep(int(40))
            continue
        elif (float(volume_ticker) < 10000000)  and (float(balances_kupili) < 2) and (float(balances_kupili_prodaje) < 2):
            print("float(volume_ticker) < 10000000:",volume_ticker)
            if int(t) <11:
                t = int(t) + 1
            else:
                t=0
            print("t",t)
            x = 0
            i = 0
            for x in open_orders2:
                user_open_orders_order_id = open_orders2[i]['orderId']
                user_open_orders_type = open_orders2[i]['side']
                print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                            
                if user_open_orders_type == "BUY":
                    print ("Удаляем ордер:", user_open_orders_order_id)
                    order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                    print(order_cancel)
                i = i + 1
                print("i=",i)
            filehandle = open('N.txt', 'w')
            filehandle.write(str(t))
            filehandle.close()
            time.sleep(int(40))
            continue
        else:
            print("Покупаем")
    
    if  (float(ADX_SUMA2)>7) or (float(CCI20) < -200) or (float(ADX_DI2) > 30):
        print("(ADX_SUMA>5:",ADX_SUMA2,")","(CCI20 <-200:",CCI20,")","(","ADX-DI>30:",ADX_DI2,")")
        x = 0
        i = 0
        for x in open_orders2:
            user_open_orders_order_id = open_orders2[i]['orderId']
            user_open_orders_type = open_orders2[i]['side']
            print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
                        
            if user_open_orders_type == "BUY":
                print ("Удаляем ордер:", user_open_orders_order_id)
                order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                print(order_cancel)
            i = i + 1
            print("i=",i)
        if int(t) <11:
            t = int(t) + 1
        else:
            t=0
        print("t",t)
        filehandle = open('N.txt', 'w')
        filehandle.write(str(t))
        filehandle.close()
        print("МОИ ЗАКАЗЫ ОТКРЫТЫЕ")
        print("")
        print("|  Тип операции   | Валютная пара   |      Цена       |   Количество    |     Сумма     |")

        x = 0
        i = 0
        suma = 0
        suma2 = 0
        suma3 = 0
        for x in open_orders2:
            my_type = open_orders2[i]['side']
            my_h_pair = open_orders2[i]['symbol']
            my_price = open_orders2[i]["price"]
            my_quantity = open_orders2[i]["origQty"]
            my_amount = float(my_price)*float(my_quantity)
            my_amount2 = str(round(my_amount,5))
            if my_type == 'BUY':
                suma2 = float(suma2) + float(my_quantity)
            if my_type == 'SELL':
                suma3 = float(suma3) + float(my_quantity)
            suma = float(suma) + float(my_amount)
            i=i+1 
            print("|",str(my_type)," "*(14-len(my_type)),"|",str(my_h_pair)," "*(14-len(my_h_pair)),"|",my_price," "*(14-len(my_price)),"|",my_quantity," "*(14-len(my_quantity)),"|",my_amount2," "*(12-len(my_amount2)),"|")

        print("")   
        print("ТОРГОВЛЯ ИСТОРИЯ")
        print("")
        print("|  Тип операции   | Валютная пара   |       Цена      |   Количество    |   Сумма       |")

        x = 0
        v = -1
        
        if kolicHistory > 10:
            kolicHistory = 10
        else:
            print(" ")

        while v > (kolicHistory*-1):
            my_h_type = TradeHistory2[v]['commissionAsset']
            my_h_pair = TICKER
            my_h_price = TradeHistory2[v]['price']
            my_h_quantity = TradeHistory2[v]['qty']
            my_h_amount = float(my_h_price)*float(my_h_quantity)
            my_h_amount2 = str(round(my_h_amount,5))

            v = v - 1 
            print("|",my_h_type," "*(14-len(my_h_type)),"|",my_h_pair," "*(14-len(my_h_pair)),"|",my_h_price," "*(14-len(my_h_price)),"|",my_h_quantity," "*(13-len(my_h_quantity))," |",my_h_amount2," "*(12-len(my_h_amount2)),"|")
        
        time.sleep(int(40))
        continue
    ##### Подключаем end TradingView - Analyze Your Chart ########################    
    
    ###### считаем среднию #########################################
    i = -1
    RTHistory = 0
    RTHistoryvol = 0
    volume = 0
    volume2 = 0
    srednia = 0
    RTHistoryvol_suma = 0
    ordN = 0
    RTHistoryvol_o = 0
    #Запрашиваем историю ордеров
    x = 0
    for x in TradeHistory2:
        ordN = TradeHistory2[i]['commissionAsset']
        #print ("Проверяем если есть BTC:", ordN)
        if float(balances_kupili_prodaje)-1 > float(RTHistoryvol_suma):
            if ordN == PARA or ordN == 'BNB':
                RTHistory = TradeHistory2[i]['price'] #Запрашиваем цену купленого ордера
                #print("RTHistory",RTHistory)
                RTHistoryvol = TradeHistory2[i]['qty'] #Запрашиваем количества купленого ордера
                #print ("Запрашиваем количества битковина купленого ордера:", RTHistoryvol)
                volume = volume + (float(RTHistory)*float(RTHistoryvol))
                #print ("volume", volume)
                volume2 = volume2 + float(RTHistoryvol)
                #print ("volume2", volume2)
                srednia = volume / volume2

                RTHistoryvol_suma = float(RTHistoryvol_suma) + float(RTHistoryvol)
                #print ("Запрашиваем сумму количества битковина купленого ордера:", RTHistoryvol_suma)   
            else:
                print("ПРОПУСКАЕМ")
        else:
            print("")
            break
        i = i - 1
        #print("i=",i)
        #print ("Средния цена", srednia)
    ###################################################
    try:
        RTHistory = TradeHistory2[-1]['commissionAsset']
    except Exception:
        currentPrice = client.get_order_book(symbol=TICKER)['bids'][0][0]
        cena = 0
        cena = float(currentPrice) - float((float(currentPrice)/100*float(ord_otstup1)))
        amount = 0
        amount = float(btc_total)/float(cena)
        amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
        order = client.order_market_buy(symbol=TICKER,quantity=amount_round)
        print ("Созданный первый ордер:", order)
        time.sleep(5)
        continue
    #print ("Средния цена из истории", RTHistoryvol_o)
    if float(srednia) < float(RTHistoryvol_o):
        srednia = RTHistoryvol_o
        #print ("Средния цена новая", srednia)
    ###################################################
    #print("high",high)
    #print ("Средния цена", srednia)
    #print("RSI",RSI)
    ###### конец считаем среднию #########################################

    ##################################################################################################################################################
    
    ###################################################
    RTHistory = 0
    try:
        RTHistory = TradeHistory2[-1]['commissionAsset']
    except Exception:
        currentPrice = client.get_order_book(symbol=TICKER)['bids'][0][0]
        cena = 0
        cena = float(currentPrice) - float((float(currentPrice)/100*float(ord_otstup1)))
        amount = 0
        amount = float(btc_total)/float(cena)
        amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
        order = client.order_market_buy(symbol=TICKER,quantity=amount_round)
        print ("Созданный первый ордер:", order)
    #print("Получение сделок пользователя:", RTHistory)
    currentPrice = client.get_order_book(symbol=TICKER)['bids'][0][0]
    #print ("Цена bids", currentPrice)

    if kolic == 0 and kolic !=1 and (RTHistory == CURRENCY or RTHistory == "BNB") and float(balances_kupili) < 2 and float(balances_kupili_prodaje) < 2:

        print ("ЗАПУСК ПРОГРАММЫ ДОБАВЛЯТЬ ПЕРВЫЕ ОРДЕРА")

        currentPrice = 0
        currentPrice = pervii_order #client.get_order_book(symbol=TICKER)['bids'][0][0]
        #print ("Цена bids", currentPrice)
        cena = 0
        cena = float(currentPrice) - float((float(currentPrice)/100*float(ord_otstup1)))
        #print ("Цена первого ордера",  Decimal('{:.4f}'.format(Decimal(cena))))
        amount = 0
        amount = float(btc_total)/float(cena)
        amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
        #print("amount_round:", amount_round)
        cena_round = Decimal(str(cena_round_colicestvo).format(Decimal(cena)))
        #print("cena_round:", cena_round)
        order = client.order_limit_buy(symbol=TICKER,quantity=amount_round,price=cena_round)
        print ("Созданный первый ордер:", order)
        time.sleep(20)
        continue

        
        
        cena2 = 0
        AMT2 = 0
        ordN2 = 0
        amount2 = 0
        cena2 = float(currentPrice) - float((float(currentPrice)/100 * (float(ord_otstup2)+float(ord_otstup1))))
        #print ("Цена второго ордера", Decimal('{:.4f}'.format(Decimal(cena2))))
        cena_round = Decimal(str(cena_round_colicestvo).format(Decimal(cena2)))
        #print("cena_round2:", cena_round2)
        amount2 = 0
        amount2 = float(btc_total)/float(cena)*float(btc_proc_uvilic)
        amount_round2 = Decimal('{:.0f}'.format(Decimal(amount2)))
        #print("amount_round2:", amount_round2)
        order2 = client.order_limit_buy(symbol=TICKER,quantity=amount_round2,price=cena_round2)
        print ("Созданный ордер:", order2)
        
        time.sleep(int(interval_info))
        time.sleep(20)
        continue
        

        print ("КОНЕЦ ПРОГРАММЫ ДОБАВЛЯТЬ ПЕРВЫЕ ОРДЕРА")


    kb = 0
    ordN_sell = 0
    kb_price = 0
    try:
        ordN_sell = open_orders2[-1]["side"]
        ##print(ordN_sell)
        if ordN_sell == 'BUY':
            kb_price = open_orders2[-1]["price"]
            ##print("kb_price",kb_price)
            kb_amount = open_orders2[-1]["origQty"]
            ##print(kb_amount)
            kb = float(kb_price)*float(kb_amount)
            ##print("kb",kb)
        else:
            kb_price = open_orders2[-2]["price"]
            kb_amount = open_orders2[-2]["origQty"]
            kb = float(kb_price)*float(kb_amount)
            ##print("kb",kb)
    except Exception:
        print("")
        
    if (float(kb_price) > float(poslednii_order)) and (int(kolic) < int(btc_ord_2)) and kolic != 1 and kolic != 0 and (float(balances) > (float(kb)*float(btc_proc_uvilic))):
                
        print ("ЗАПУСК ПРОГРАММЫ ДОБАВЛЯТЬ ОРДЕРА ВНИЗ")

            
        i = 0
        cena = 0
        AMT = 0
        kb = 0
        ordN_sell2 = 0
        ordN_sell = 0
        ordN = 0

        #print("Доступна:", balances)
        try:
            pribil = float(suma_RUB)
            #print("Сколько у меня денег suma_RUB:", suma_RUB)
        except Exception:
            pribil = 0.2
            #print("Сколько у меня денег pribil:", pribil)

        atap1 = 0
        atap2 = 0
        atap3 = 0
        atap1 = float(pribil)/6
        atap2 = float(pribil)/4
        atap3 = float(pribil)/3
        #print("--------------------------------------------------------")
        #print("Первый этап:",atap1)
        #print("Второй этап:",atap2)
        #print("Третий этап:",atap3)
        #print("--------------------------------------------------------")
        #print("********************************************************")
        scoli_stavim1 = 0
        scoli_stavim1 = float(pribil)-float(atap1)
        #print("Сколько будет длится первый этап",scoli_stavim1)

        scoli_stavim2 = 0
        scoli_stavim2 = float(pribil)-float(atap2)
        #print("Сколько будет длится второй этап",scoli_stavim2)

        scoli_stavim3 = 0
        scoli_stavim3 = float(pribil)-float(atap3)
        #print("Сколько будет длится третий этап",scoli_stavim3)
        #print("********************************************************")
        ################################################### 

        #------------------------------------------------------------
        if float(balances) > float(scoli_stavim1):
            print("Первый этап:",atap1)
            #print("Сколько будет длится первый этап",scoli_stavim1)
            #print("Доступна:",balances)
            #print("Процент между ордерами:",ord_otstup2)
            #print("Количество ордеров. Если будет меньше, то будет добавлять:",btc_ord_2)
        elif float(scoli_stavim1) > float(balances) > float(scoli_stavim2):
            #print("Второй этап:",atap2)
            #print("Сколько будет длится второй этап",scoli_stavim2)
            #print("Доступна:",balances)
            #ord_otstup2 = cfg['otstup-vtorogo']['p2']
            ord_otstup2 = float(ord_otstup2) * 1#2
            print("Процент между ордерами:",ord_otstup2)
            #print("Количество ордеров. Если будет меньше, то будет добавлять:",btc_ord_2)
        elif float(scoli_stavim2) > float(balances) > float(scoli_stavim3):
            #print("Третий этап:",atap3)
            #print("Сколько будет длится третий этап",scoli_stavim3)
            #print("Доступна:",balances)
            #ord_otstup2 = cfg['otstup-vtorogo']['p2']
            ord_otstup2 = float(ord_otstup2) * 1#3
            #print("Процент между ордерами:",ord_otstup2)
            #print("Количество ордеров. Если будет меньше, то будет добавлять:",btc_ord_2)
        else:
            #ord_otstup2 = cfg['otstup-vtorogo']['p2']
            #print("Количество ордеров. Если будет меньше, то будет добавлять:",btc_ord_2)
            #print("Сколько будет длится четвертый этап до",0)
            ord_otstup2 = float(ord_otstup2) * 1#4
            #print("Процент между ордерами:",ord_otstup2)
        #########################################################

        ordN_sell2 = open_orders2[-1]["side"]
        if ordN_sell2 == 'BUY':
            ordN = open_orders2[-1]['price']
            #print("Цена уже нового ордера ordN:", ordN)
                
            kb = open_orders2[-1]['origQty']  #0.0015 количества битковина Trade_Client.active_orders()[0]['price']
            #print("Количества в последнем отрытом ордере:", kb)
            time.sleep(int(interval_info2))
            cena = float(ordN) - (float(ordN)/100 * float(ord_otstup2))
            #print("Цена уже нового ордера:", Decimal('{:.4f}'.format(Decimal(cena))))
            cena_round = Decimal(str(cena_round_colicestvo).format(Decimal(cena)))
            print("cena_round:", cena_round)
            amount = 0
            amount = float(kb)*float(btc_proc_uvilic)
            amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
            #print("amount_round:", amount_round)
            order = client.order_limit_buy(symbol=TICKER, quantity=amount_round, price=cena_round)
            #print ("Добавленый ордер:", order)
            time.sleep(int(interval_info2))
            time.sleep(20)
            continue
        else:
            ordN = open_orders2[-2]['price']
            #print("Цена уже нового ордера ordN:", ordN)
                
            kb = open_orders2[-2]['origQty']  #0.0015 количества битковина Trade_Client.active_orders()[0]['price']
            #print("Количества в последнем отрытом ордере:", kb)
            time.sleep(int(interval_info2))
            cena = float(ordN) - (float(ordN)/100 * float(ord_otstup2))
            #print("Цена уже нового ордера:", Decimal('{:.4f}'.format(Decimal(cena))))
            cena_round = Decimal(str(cena_round_colicestvo).format(Decimal(cena)))
            print("cena_round:", cena_round)
            amount = 0
            amount = float(kb)*float(btc_proc_uvilic)
            amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
            #print("amount_round:", amount_round)
            order = client.order_limit_buy(symbol=TICKER, quantity=amount_round, price=cena_round)
            print ("Добавленый ордер:", order)
            time.sleep(int(interval_info2))
            time.sleep(20)
            continue
            
        print ("КОНЕЦ ПРОГРАММЫ ДОБАВЛЯТЬ ОРДЕРА ВНИЗ")
        time.sleep(20)
        continue

    

    ordN_sell = 0
    ordN_sell2 = 0
    ordN_sell3 = 0
    try:
        ordN_sell = open_orders2[0]["side"]
        ordN_sell2 = open_orders2[-1]["side"]
        ordN_sell3 = TradeHistory2[-1]['commissionAsset']
    except Exception:
        print("")
    #print(ordN_sell)
    #print(ordN_sell2)
    #print(ordN_sell3)
    #print(kolic)
    
    
    RTHistory2 = 0
    RTHistory6 = 0
    RTHistory = 0
    try:
        RTHistory2 = open_orders2[-1]["side"]
        RTHistory6 = open_orders2[0]["side"]
        RTHistory = TradeHistory2[-1]['commissionAsset']
    except Exception:
        
        RTHistory2 = "SELL"
        RTHistory6 = "SELL"
        RTHistory = PARA2
        kolic = 1
        
        #print("Ошибка ДОКУПАТЬ")

    #print("RTHistory2",RTHistory2)
    #print("RTHistory6",RTHistory6)
    #print("RTHistory",RTHistory)
    
    if RTHistory2 == "SELL" and RTHistory6 == "SELL" and kolic == 1 and (RTHistory == "BNB" or RTHistory == PARA):
            
        print ("ЗАПУСК ПРОГРАММЫ ДОКУПАТЬ ОРДЕРА")
        
        kb = 0
        kb = TradeHistory2[-1]['qty']  #0.0015 количества битковина
        #print("Количества в последнем ордере в истории:", kb)
        ordN = 0
        ordN = TradeHistory2[-1]['price']
        #print ("Цена последнего ордера:", ordN)
        cena = 0
        cena = float(ordN) - (float(ordN)/100 * float(ord_otstup2))
        #print("Цена уже нового ордера:", Decimal('{:.4f}'.format(Decimal(cena))))
        cena_round = Decimal(str(cena_round_colicestvo).format(Decimal(cena)))
        #print("cena_round:", cena_round)
        amount = 0
        amount = float(kb)*float(btc_proc_uvilic)
        amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
        #print("amount_round:", amount_round)
        try:
            order = client.order_limit_buy(symbol=TICKER, quantity=amount_round, price=cena_round)
            #print ("Созданный ордер докупать:", order)
        except Exception:
            #print("Ошибка Созданный ордер докупать")
            amount = 0
            amount = float(btc_total)/float(cena)
            amount_round = Decimal('{:.0f}'.format(Decimal(amount)))
            order = client.order_limit_buy(symbol=TICKER, quantity=amount_round, price=cena_round)
            print ("Созданный ордер докупать:", order)
        ##################################################
        time.sleep(20)
        continue
        print ("КОНЕЦ ПРОГРАММЫ ДОКУПАТЬ ОРДЕРА")
        
    if RTHistory2 == "BUY" and RTHistory6 == "BUY" and kolic == 1 and (RTHistory == "BNB" or RTHistory == CURRENCY):
                
        #print ("ЗАПУСК ПРОГРАММЫ УДАЛЕНИЕ ОРДЕРА")
        #print ("Количества ордеров:", kolic)
        i = 0   
        
        while i <= kolic:  
            user_open_orders = 0
            try:
                user_open_orders = open_orders2[i]['orderId']
                #print("Какие orderId:",user_open_orders)
                
                order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders))
                #print("удаление ордера:", order_cancel)
            except Exception:
                print("Ошибка удаление ордера")
            
            i= i + 1
            #print(i)

        #print ("КОНЕЦ ПРОГРАММЫ УДАЛЕНИЕ ОРДЕРА")
    
    #########################Проверяим совпадает цена первого ордера и указана из файла#############################
    pervii_order_cena = open_orders2[0]["price"]
    #print("Первый ордер выставлен",pervii_order_cena)
    #print("Первый ордер прописан в CFG", pervii_order)
    #print("RTHistory6",RTHistory6)
    #print(ordN_sell)
    #print(ordN_sell2)
    #print(ordN_sell3)
    
    if ordN_sell == "BUY" and ordN_sell2 == "BUY" and (ordN_sell3 == CURRENCY or ordN_sell3 == "BNB") and kolic !=1 and kolic !=0 and float(balances_kupili) < 2 and float(balances_kupili_prodaje) < 2:
        if float(pervii_order) != float(pervii_order_cena):
            #print ("ЗАПУСК ПРОГРАММЫ УДАЛЕНИЕ ОРДЕРА")
            print ("Количества ордеров:", kolic)
            i = 0   
            
            while i < kolic:  
                user_open_orders = 0
                user_open_orders = open_orders2[i]['orderId']
                #print("Какие orderId:",user_open_orders)
                    
                order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders))
                #print("Созданный ордер:", order_cancel)
                    
                i= i + 1
                #print(i)
        
    ######################################################
    ############################################# Зашита от повторение ордера ###################
     
    price_proverka = 0
    user_open_orders_order_price = 0
                  
    user_open_orders_order_price = open_orders2[-1]['price']
    #print(user_open_orders_order_price)
    try:
        price_proverka = open_orders2[-2]['price'] 
    except Exception:
        print("Ошибка удаление ордера")
    #print(price_proverka)
    x = 0
    i = 0
    if user_open_orders_order_price == price_proverka :
        for x in open_orders2:   
            user_open_orders_order_id = open_orders2[i]['orderId']
            user_open_orders_type = open_orders2[i]['side']
            ##print("Какой ордер стаит первый если sell удаляим ордер:",user_open_orders_type)
            
            if user_open_orders_type == "BUY":
                ##print ("Удаляем ордер:", user_open_orders_order_id)
                order_cancel = client.cancel_order(symbol=TICKER, orderId=int(user_open_orders_order_id))
                ##print(order_cancel)
           
            i = i + 1
            #print("i=",i)
    #############################################################################################
    
    
    ###################################################################################

    print("#############################################", l ,"#######################################")
    print("МОИ ЗАКАЗЫ ОТКРЫТЫЕ")
    print("")
    print("|  Тип операции   | Валютная пара   |      Цена       |   Количество    |     Сумма     |")

    x = 0
    i = 0
    suma = 0
    suma2 = 0
    suma3 = 0
    for x in open_orders2:
        my_type = open_orders2[i]['side']
        my_h_pair = open_orders2[i]['symbol']
        my_price = open_orders2[i]["price"]
        my_quantity = open_orders2[i]["origQty"]
        my_amount = float(my_price)*float(my_quantity)
        my_amount2 = str(round(my_amount,5))
        if my_type == 'BUY':
            suma2 = float(suma2) + float(my_quantity)
        if my_type == 'SELL':
            suma3 = float(suma3) + float(my_quantity)
        suma = float(suma) + float(my_amount)
        i=i+1 
        print("|",str(my_type)," "*(14-len(my_type)),"|",str(my_h_pair)," "*(14-len(my_h_pair)),"|",my_price," "*(14-len(my_price)),"|",my_quantity," "*(14-len(my_quantity)),"|",my_amount2," "*(12-len(my_amount2)),"|")

    print("")   
    print("ТОРГОВЛЯ ИСТОРИЯ")
    print("")
    print("|  Тип операции   | Валютная пара   |       Цена      |   Количество    |   Сумма       |")

    x = 0
    v = -1
    
    if kolicHistory > 10:
        kolicHistory = 10
    else:
        print(" ")

    while v > (kolicHistory*-1):
        my_h_type = TradeHistory2[v]['commissionAsset']
        my_h_pair = TICKER
        my_h_price = TradeHistory2[v]['price']
        my_h_quantity = TradeHistory2[v]['qty']
        my_h_amount = float(my_h_price)*float(my_h_quantity)
        my_h_amount2 = str(round(my_h_amount,5))

        v = v - 1 
        print("|",my_h_type," "*(14-len(my_h_type)),"|",my_h_pair," "*(14-len(my_h_pair)),"|",my_h_price," "*(14-len(my_h_price)),"|",my_h_quantity," "*(13-len(my_h_quantity))," |",my_h_amount2," "*(12-len(my_h_amount2)),"|")
    """
    print("Количество выставленого на покупку ",suma2)
    print("Количество купленого",suma3)
    print("Количество купленого и выставленого",suma3+suma2)
    print("Баланс пользователя в ордерах USDT",suma)
    suma_RUB = float(balances) + float(suma)
    print("Сколько у меня денег:", suma_RUB)

    print ("Средния цена", srednia)
    print ("Текушая цена", currentPrice)
    print("Сколько на балансе:",suma3)
    """
    suma_RUB = float(balances) + float(suma)
    print("Баланс пользователя в ордерах USDT",suma)
    print("Сколько у меня денег:", suma_RUB)
    print("RSI:",RSI)
    
    """
    print("low:",low)
    print("EMA200:",EMA200)
    print("CCI20:",CCI20)
    print("Volume:",volume_)
    print("CCI20max-1:",CCI20max_1)
    print("CCI20min-1:",CCI20min_1)
    print ("Интервал:", R)
    print("CCI20max-5:",CCI20max_5)
    print("CCI20min-5:",CCI20min_5)
    print ("Интервал:", R)
    print("ADX+:",abs(ADX_DI))
    print("ADX_DI+max1:",ADX_DImax_1)
    print("ADX_DI-max1:",ADX_DI2max_1)
    print("ADX-:",abs(ADX_DI2))
    print("ADX_DI+max5:",ADX_DImax_5)
    print("ADX_DI-max5:",ADX_DI2max_5)
    """

    print("ADX_SUMAmax5:",ADX_SUMAmax5)
    print("ADX_DI+max5:",ADX_DImax5)
    print("ADX_DI-max5:",ADX_DI2max5)
    print("Прочент продажи",procen_prodaji)
    print("Recommend.All:",RecommendAll)
    print("Recommend.MA:",RecommendMA)
    print("AO:",AO)
    print("P.SAR:",P_SAR)
    print("BB.lower:",BB_lower)
    print ("Средния цена", srednia)
    
    print("vse","Интервал:", R,PARA,volume_ticker)
    if int(t) <11:
        t = int(t) + 1
    else:
        t=0
    print("t",t)
    filehandle = open('N.txt', 'w')
    filehandle.write(str(t))
    filehandle.close()
    time.sleep(int(40))
else:
    print("---------------------------Не тот кошелек или маленький объем-----------------------")    

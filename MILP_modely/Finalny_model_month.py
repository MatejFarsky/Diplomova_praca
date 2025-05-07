import math
import time as tm
import numpy as np
import pandas as pd
from amplpy import AMPL, Environment

def round_dw(x, dec):
    return math.floor(x * 10**dec) / 10**dec

def load_data(date):
    df = pd.read_csv('2023_06_ID_Trades.csv', sep=';')
    df_filter = df[(df['DeliveryStartDay'] == date) & (df['ProductName'] == 'XBID_Quarter_Hour_Power')]
    exe_unique = pd.unique(df_filter.loc[:, 'ExecutionTime'])
    df1 = pd.read_excel('Data_input.xlsx',sheet_name=date)
    return df_filter, exe_unique, df1

def solve_battery(n, price_bid, price_ask, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c, restrict):
    ampl = AMPL(Environment('C:\\Users\\Matej\\AMPL'))
    ampl.read('bateria_v3.mod')
    
    ampl.getParameter('n').setValues([n])
    ampl.getParameter('price_bid').setValues(price_bid)
    ampl.getParameter('price_ask').setValues(price_ask)
    ampl.getParameter('buy_prev').setValues(buy_prev)
    ampl.getParameter('sell_prev').setValues(sell_prev)
    ampl.getParameter('cap_0').setValues([cap_0])
    ampl.getParameter('cap_n').setValues([cap_n])
    ampl.getParameter('Lower_cap').setValues([Lower_cap])
    ampl.getParameter('Upper_cap').setValues([Upper_cap])
    ampl.getParameter('Upper_buy').setValues([Upper_buy])
    ampl.getParameter('Upper_sell').setValues([Upper_sell])
    ampl.getParameter('alpha').setValues([alpha])
    ampl.getParameter('beta').setValues([beta])
    ampl.getParameter('c').setValues([c])
    ampl.getParameter('restrict').setValues(restrict)
    
    ampl.solve()
    
    vari = ampl.getVariable('cap').getValues().toList()
    cap_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('buy_cycles').getValues().toList()
    buy_cycles_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('sell_cycles').getValues().toList()
    sell_cycles_opt = [vari[t][1] for t in range(len(vari))]
    
    vari = ampl.getVariable('buy').getValues().toList()
    buy_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('sell').getValues().toList()
    sell_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('buy_or_sell').getValues().toList()
    buy_or_sell_opt = [vari[t][1] for t in range(len(vari))]
    
    opt_val = ampl.get_value('obj_fun')

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val

def iteration(tm,df1,restrict):
    start = tm.time()
    
    #Presnost
    dec = 2
    
    #Nacitanie dat
    price_bid, price_ask, buy_prev, sell_prev = df1.loc[:,"price_bid"], df1.loc[:,"price_ask"], df1.loc[:,"buy_prev"], df1.loc[:,"sell_prev"]
    
    #Definovanie parametrov
    alpha, beta = 0.92, 0.93
    vykon = 1
    cap_0 = 0.5   #pociatocna podmienka
    cap_n = 0.5   #koncova podmienka
    Lower_cap, Upper_cap = 0, 1
    Upper_sell, Upper_buy = round_dw(vykon / 4 * beta, dec), round_dw(vykon / 4, dec)
    c = 2       #max pocet cyklov
    n = len(price_bid)
    
    #Solving
    cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val = solve_battery(n, price_bid, price_ask, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c, restrict)
    
    stop = tm.time()
    time = stop - start

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, time

def calculate_day(date):
    df_filter, exe_unique, df1 = load_data(date)
    df2 = pd.DataFrame({
        'ExeTime': 'Spot',
        'Profit': [0],
        'Time': [0]
    })

    for i in range(len(exe_unique)):
        restrict = pd.Series(np.zeros(len(df1.price_bid)))
        current = df_filter[df_filter['ExecutionTime'] == exe_unique[i]]
        current = current.drop_duplicates(subset='DeliveryStartTime', keep='last')
        for j in range(len(current.Price)):
            if float(current.Price.iloc[j].replace(',', '.')) > 0:
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_bid'] = 0.995 * float(current.Price.iloc[j].replace(',', '.'))
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_ask'] = 1.005 * float(current.Price.iloc[j].replace(',', '.'))
            else:
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_bid'] = 1.005 * float(current.Price.iloc[j].replace(',', '.'))
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_ask'] = 0.995 * float(current.Price.iloc[j].replace(',', '.'))
            restrict[df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'Unnamed: 0']] = 1
        cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, time = iteration(tm,df1,restrict)
        df1.buy_prev = pd.Series(np.add(buy_opt, df1.loc[:,"buy_prev"].tolist()))
        df1.sell_prev = pd.Series(np.add(sell_opt, df1.loc[:,"sell_prev"].tolist()))
        df2.loc[len(df2.index)] = [current.ExecutionTime.iloc[0], opt_val, time]

    with pd.ExcelWriter('Data_output.xlsx', mode='a', if_sheet_exists='replace') as writer:
        df2.to_excel(writer, sheet_name=date)

#main
dates = ['2023.06.01','2023.06.02','2023.06.03','2023.06.04','2023.06.05','2023.06.06','2023.06.07','2023.06.08','2023.06.09','2023.06.10',
         '2023.06.11','2023.06.12','2023.06.13','2023.06.14','2023.06.15','2023.06.16','2023.06.17','2023.06.18','2023.06.19','2023.06.20',
         '2023.06.21','2023.06.22','2023.06.23','2023.06.24','2023.06.25','2023.06.26','2023.06.27','2023.06.28','2023.06.29','2023.06.30']
for d in range(len(dates)):
    calculate_day(dates[d])

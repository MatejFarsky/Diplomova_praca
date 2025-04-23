import math
import time as tm
import numpy as np
import pandas as pd
from amplpy import AMPL, Environment


def round_dw(x, dec):
    return math.floor(x * 10**dec) / 10**dec

def load_data():
    df = pd.read_csv('2023_06_ID_Trades.csv', sep=';')
    df_filter = df[(df['DeliveryStartDay'] == '2023.06.04') & (df['ProductName'] == 'XBID_Quarter_Hour_Power')]
    df_filter['ExecutionTime'] = pd.to_datetime(df_filter['ExecutionTime'], format='%Y.%m.%d %H:%M')
    exe_unique = pd.unique(df_filter.loc[:, 'ExecutionTime'])
    df1 = pd.read_excel('Data_input.xlsx')
    tradab = pd.read_excel('Tradability_1h.xlsx')
    mean_prices = pd.read_excel('Mean_prices.xlsx')
    spot_prices = pd.read_excel('Spot_prices.xlsx')
    return df_filter, exe_unique, df1, tradab, mean_prices, spot_prices

def solve_battery(n, m, prices_bid, prices_ask, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c, restrict_buy, restrict_sell):
    ampl = AMPL(Environment('C:\\Users\\Matej\\AMPL'))
    ampl.read('bateria_v6.mod')
    
    ampl.getParameter('n').setValues([n])
    ampl.getParameter('m').setValues([m])
    ampl.getParameter('price_bid').setValues(prices_bid.to_numpy())
    ampl.getParameter('price_ask').setValues(prices_ask.to_numpy())
    ampl.getParameter('buy_prev_0t').setValues(buy_prev)
    ampl.getParameter('sell_prev_0t').setValues(sell_prev)
    ampl.getParameter('cap_0').setValues([cap_0])
    ampl.getParameter('cap_n').setValues([cap_n])
    ampl.getParameter('Lower_cap').setValues([Lower_cap])
    ampl.getParameter('Upper_cap').setValues([Upper_cap])
    ampl.getParameter('Upper_buy').setValues([Upper_buy])
    ampl.getParameter('Upper_sell').setValues([Upper_sell])
    ampl.getParameter('alpha').setValues([alpha])
    ampl.getParameter('beta').setValues([beta])
    ampl.getParameter('c').setValues([c])
    ampl.getParameter('restrict_buy').setValues(restrict_buy.to_numpy())
    ampl.getParameter('restrict_sell').setValues(restrict_sell.to_numpy())
    
    ampl.solve()
    
    vari = ampl.getVariable('cap').getValues().toList()
    cap_opt = [vari[t][2] for t in range(n+1)]
    vari = ampl.getVariable('buy_cycles').getValues().toList()
    buy_cycles_opt = [vari[t][2] for t in range(n+1)]
    vari = ampl.getVariable('sell_cycles').getValues().toList()
    sell_cycles_opt = [vari[t][2] for t in range(n+1)]
    
    vari = ampl.getVariable('buy').getValues().toList()
    buy_opt = [vari[t][2] for t in range(len(vari))]
    vari = ampl.getVariable('sell').getValues().toList()
    sell_opt = [vari[t][2] for t in range(len(vari))]
    vari = ampl.getVariable('buy_or_sell').getValues().toList()
    buy_or_sell_opt = [vari[t][2] for t in range(n)]
    
    opt_val = ampl.get_value('obj_fun')
    profits = pd.Series(np.ones(m))
    for t in range(m):
        profits[t] = np.dot(np.array(sell_opt[(t*n):((t+1)*n)]), np.array(prices_bid.iloc[t, :])) - np.dot(np.array(buy_opt[(t*n):((t+1)*n)]),np.array(prices_ask.iloc[t, :]))

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profits

def save_data(df2):
    df2.to_excel('Data_output.xlsx')

def iteration(tm,df1,tradab,prices_bid,prices_ask,m):
    start = tm.time()
    
    #Presnost
    dec = 2
    
    #Nacitanie dat
    buy_prev, sell_prev = df1.loc[:,"buy_prev"], df1.loc[:,"sell_prev"]

    #Definovanie parametrov
    alpha, beta = 0.92, 0.93
    vykon = 1
    cap_0 = 0.5   #pociatocna podmienka
    cap_n = 0.5   #koncova podmienka
    Lower_cap, Upper_cap = 0, 1
    Upper_sell, Upper_buy = round_dw(vykon / 4 * beta, dec), round_dw(vykon / 4, dec)
    c = 2       #max pocet cyklov
    n = len(buy_prev)
    restrict_buy = tradab.iloc[:,1:]
    restrict_sell = tradab.iloc[:,1:]

    #Solving
    cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profits = solve_battery(n, m, prices_bid, prices_ask, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c, restrict_buy, restrict_sell)
    
    stop = tm.time()
    time = stop - start

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profits, time

#main
df_filter, exe_unique, df1, tradab, mean_prices, spot_prices = load_data()
df2 = pd.DataFrame({
    'ExeTime': 'Spot',
    'Profit': [119.88276]
})

m = len(tradab['time'])
prices_bid = pd.DataFrame(index=range(m), columns=mean_prices.columns[1:])
prices_bid.iloc[0,:] = df1.loc[:,'price_bid']
prices_ask = pd.DataFrame(index=range(m), columns=mean_prices.columns[1:])
prices_ask.iloc[0,:] = df1.loc[:,'price_ask']
exe_ind = 0
for i in range(m):
    tradab.iloc[i, 1:] = 0
    if i>0:
        prices_bid.iloc[i, :] = prices_bid.iloc[i-1, :]
        prices_ask.iloc[i, :] = prices_ask.iloc[i-1, :]
    if pd.to_datetime(exe_unique[exe_ind], format='%Y.%m.%d %H:%M').strftime('%X')==tradab['time'].iloc[i].strftime('%X'):
        current = df_filter[df_filter['ExecutionTime'] == exe_unique[exe_ind]]
        current = current.drop_duplicates(subset='DeliveryStartTime', keep='last')
        colidx = pd.Series(np.ones(len(current.Price)))
        for j in range(len(current.Price)):
            colidx[j] = prices_bid.columns.get_loc(pd.to_datetime(current['DeliveryStartTime'].iloc[j], format='%H:%M').time())
            prices_bid.iloc[i, int(colidx[j])] = 0.995 * float(current.Price.iloc[j].replace(',', '.'))
            prices_ask.iloc[i, int(colidx[j])] = 1.005 * float(current.Price.iloc[j].replace(',', '.'))
            tradab.loc[i, pd.to_datetime(current['DeliveryStartTime'].iloc[j], format='%H:%M').time()] = 1
        if exe_ind != (len(exe_unique)-1):
            exe_ind += 1

cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profits, time = iteration(tm,df1,tradab,prices_bid,prices_ask,m)
for t in range(len(profits)):
    df2.loc[len(df2.index)] = [tradab.iloc[t,0], profits[t]]

save_data(df2)

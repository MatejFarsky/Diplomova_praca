import math
import time as tm
import numpy as np
import pandas as pd
import statistics as st
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
    ampl.read('bateria_v5.mod')
    
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
    buy_opt = [vari[t][2] for t in range(n)]
    vari = ampl.getVariable('sell').getValues().toList()
    sell_opt = [vari[t][2] for t in range(n)]
    vari = ampl.getVariable('buy_or_sell').getValues().toList()
    buy_or_sell_opt = [vari[t][2] for t in range(n)]
    
    opt_val = ampl.get_value('obj_fun')
    profit = np.dot(np.array(sell_opt),np.array(prices_bid.iloc[0,:])) - np.dot(np.array(buy_opt),np.array(prices_ask.iloc[0,:]))

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profit

def iteration(tm,df1,tradab,mean_prices,spot_prices,t0,colidx):
    start = tm.time()
    
    #Presnost
    dec = 2
    
    #Nacitanie dat
    price_bid, price_ask, buy_prev, sell_prev = df1.loc[:,"price_bid"], df1.loc[:,"price_ask"], df1.loc[:,"buy_prev"], df1.loc[:,"sell_prev"]

    #Predikcie cien
    m = min(10,len(tradab['time'])-t0)
    sigma = 0.01
    pred_prices_bid = pd.DataFrame(index=range(m), columns=mean_prices.columns[1:])
    pred_prices_ask = pd.DataFrame(index=range(m), columns=mean_prices.columns[1:])
    for t in range(len(mean_prices.columns) - 1):
        if price_bid[t] > 0:
            if (t + 1) in colidx:
                coeff = 0.995
            else:
                coeff = 0.99
        else:
            if (t + 1) in colidx:
                coeff = 1.005
            else:
                coeff = 1.01
        pred_prices_bid.iloc[:,t] = coeff * price_predict(st.mean([price_bid[t],price_ask[t]]), spot_prices['HU'][t], t0, m-1, sigma, mean_prices.iloc[:, (t + 1)])
        pred_prices_ask.iloc[:,t] = (2-coeff) / coeff * pred_prices_bid.iloc[:,t]

    #Definovanie parametrov
    alpha, beta = 0.92, 0.93
    vykon = 1
    cap_0 = 0.5   #pociatocna podmienka
    cap_n = 0.5   #koncova podmienka
    Lower_cap, Upper_cap = 0, 1
    Upper_sell, Upper_buy = round_dw(vykon / 4 * beta, dec), round_dw(vykon / 4, dec)
    c = 2       #max pocet cyklov
    n = len(price_bid)
    restrict_buy = tradab.iloc[t0:(t0+m),1:]
    restrict_sell = tradab.iloc[t0:(t0+m),1:]

    #Solving
    cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profit = solve_battery(n, m, pred_prices_bid, pred_prices_ask, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c, restrict_buy, restrict_sell)
    
    stop = tm.time()
    time = stop - start

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profit, time

def price_predict(price_curr,spot_price,time_curr,period,sigma,price_mean):
    prices = pd.Series(np.ones(period + 1))
    prices[0] = price_curr
    price_mean_day = st.mean(price_mean)
    beta = min(max((price_curr - spot_price - price_mean_day)/(price_mean.iloc[time_curr] - price_mean_day),-10),10)
    for t in range(period):
        price_mean_t = price_mean.iloc[(time_curr + t) % len(price_mean)] - price_mean_day
        prices.iloc[t+1] = spot_price + price_mean_day + beta*price_mean_t + np.random.normal(0,sigma,1)
    return prices

#main
np.random.seed(474747)
df_filter, exe_unique, df1, tradab, mean_prices, spot_prices = load_data()
df2 = pd.DataFrame({
    'ExeTime': 'Spot',
    'Profit': [119.88276],
    'Time': [0]
})

exe_ind = 0
for i in range(len(tradab['time'])):
    if pd.to_datetime(exe_unique[exe_ind], format='%Y.%m.%d %H:%M').strftime('%X')==tradab['time'].iloc[i].strftime('%X'):
        current = df_filter[df_filter['ExecutionTime'] == exe_unique[exe_ind]]
        current = current.drop_duplicates(subset='DeliveryStartTime', keep='last')
        colidx = pd.Series(np.ones(len(current.Price)))
        for j in range(len(current.Price)):
            if float(current.Price.iloc[j].replace(',', '.')) > 0:
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_bid'] = 0.995 * float(current.Price.iloc[j].replace(',', '.'))
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_ask'] = 1.005 * float(current.Price.iloc[j].replace(',', '.'))
            else:
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_bid'] = 1.005 * float(current.Price.iloc[j].replace(',', '.'))
                df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j], 'price_ask'] = 0.995 * float(current.Price.iloc[j].replace(',', '.'))
            colidx[j] = mean_prices.columns.get_loc(pd.to_datetime(current['DeliveryStartTime'].iloc[j], format='%H:%M').time())
        cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, profit, time = iteration(tm,df1,tradab,mean_prices,spot_prices,i,colidx)
        df1.buy_prev = pd.Series(np.add(buy_opt, df1.loc[:,"buy_prev"].tolist()))
        df1.sell_prev = pd.Series(np.add(sell_opt, df1.loc[:,"sell_prev"].tolist()))
        df2.loc[len(df2.index)] = [current.ExecutionTime.iloc[0], profit, time]
        if exe_ind != (len(exe_unique)-1):
            exe_ind += 1

df2.to_excel('Data_output.xlsx')
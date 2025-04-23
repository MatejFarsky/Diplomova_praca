import pandas as pd
import time as tm

def load_data():
    df = pd.read_csv('2023_06_ID_Trades.csv', sep=';')
    df_filter = df[(df['DeliveryStartDay'] == '2023.06.04') & (df['ProductName'] == 'XBID_Quarter_Hour_Power')]
    exe_unique = pd.unique(df_filter.loc[:, 'ExecutionTime'])
    df1 = pd.read_excel('Data_input.xlsx')
    return df_filter, exe_unique, df1

#ORDERED SOLUTION
def iteration(df1,df):
    dec = 11
    alpha, beta = 0.92, 0.93
    cap_0 = 0.5  # pociatocna podmienka
    Lower_cap, Upper_cap = 0, 1
    profit_all = 0

    for k in range(len(df.buy_prev)):
        for j in range(len(df.buy_prev)-k-1):
            df_try = df1.copy()
            df_try.loc[df_try.time == df.time[k], 'buy_prev'] = df.buy_prev[k+j+1]
            df_try.loc[df_try.time == df.time[k],'sell_prev'] = df.sell_prev[k+j+1]
            df_try.loc[df_try.time == df.time[k+j+1],'buy_prev'] = df.buy_prev[k]
            df_try.loc[df_try.time == df.time[k+j+1],'sell_prev'] = df.sell_prev[k]
            profit = df_try.loc[df_try.time == df.time[k],'price'].values[0]*(df_try.loc[df_try.time == df.time[k],'sell_prev'].values[0] - df_try.loc[df_try.time == df.time[k], 'buy_prev'].values[0])
            profit += df_try.loc[df_try.time == df.time[k+j+1],'price'].values[0]*(df_try.loc[df_try.time == df.time[k+j+1],'sell_prev'].values[0] - df_try.loc[df_try.time == df.time[k+j+1], 'buy_prev'].values[0])
            profit_orig = df1.loc[df1.time == df.time[k],'price'].values[0]*(df1.loc[df1.time == df.time[k],'sell_prev'].values[0] - df1.loc[df1.time == df.time[k], 'buy_prev'].values[0])
            profit_orig += df1.loc[df1.time == df.time[k+j+1],'price'].values[0]*(df1.loc[df1.time == df.time[k+j+1],'sell_prev'].values[0] - df1.loc[df1.time == df.time[k+j+1], 'buy_prev'].values[0])
            if profit > profit_orig:
                cap = cap_0
                for l in range(len(df_try.price)):
                     cap += round(df_try.buy_prev[l]*alpha - df_try.sell_prev[l]/beta, dec)
                     if round(cap,dec) > Upper_cap or round(cap,dec) < Lower_cap:
                          break
                     if l==(len(df_try.price)-1):
                        df1 = df_try
                        profit_all += (profit - profit_orig)

    return df1, profit_all

#main
df_filter, exe_unique, df1 = load_data()
df2 = pd.DataFrame({
    'ExeTime': 'Spot',
    'Profit': [119.88276],
    'Time': [0]
})

for i in range(len(exe_unique)):
    current = df_filter[df_filter['ExecutionTime'] == exe_unique[i]]
    current = current.drop_duplicates(subset='DeliveryStartTime',keep='last')
    df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[0], 'price'] = float(current.Price.iloc[0].replace(',', '.'))
    df = df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[0]]
    df = df.reset_index()
    for j in range(len(current.Price)-1):
        df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j+1], 'price'] = float(current.Price.iloc[j+1].replace(',','.'))
        df = pd.concat([df,df1.loc[df1['time'] == current['DeliveryStartTime'].iloc[j+1],:]],ignore_index=True)
    if len(df.time)>1:
        start = tm.time()
        df1, opt_val = iteration(df1,df)
        stop = tm.time()
        time = stop - start
        df2.loc[len(df2.index)] = [current.ExecutionTime.iloc[0], opt_val, time]
        print(df2.loc[len(df2.index)-1])
    else:
        df2.loc[len(df2.index)] = [current.ExecutionTime.iloc[0], 0, 0]

df2.to_excel('Data_output.xlsx')

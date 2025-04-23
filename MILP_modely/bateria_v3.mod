option solver gurobi;
option show_stats 1;
option gurobi_options 'outlev=0 mipgap=0.01 timelim=5 multiobj=1' ;
option presolve_eps 1e-11;

#params
param n; #pocet casov
param price_bid{t in 0 .. n-1}; #ceny predaja
param price_ask{t in 0 .. n-1}; #ceny nakupu
param buy_prev{t in 0 .. n-1}; #predosle nakupovana kapacita
param sell_prev{t in 0 .. n-1}; #predosle predavana kapacita
param restrict{t in 0 .. n-1}; #obmedzenie obchodovatelnosti
param cap_0; #pociatocna kapacita
param cap_n; #koncova kapacita
param Lower_cap; #spodne ohranicenie kapacity
param Upper_cap; #horne ohranicenie kapacity
param Upper_buy; #ohranicenie nakupovanej kapacity
param Upper_sell; #ohranicenie predavanej kapacity
param alpha; #koeficient ucinnosti nabijania
param beta; #koeficient ucinnosti vybijania
param c; #ohranicenie poctu cyklov

var buy_or_sell{t in 0 .. n-1} binary;
var sell{t in 0 .. n-1};
var buy{t in 0 .. n-1};

var cap{t in 0 .. n} <= Upper_cap, >= Lower_cap;
var buy_cycles{t in 0 .. n} <= c * (Upper_cap - Lower_cap), >= 0;
var sell_cycles{t in 0 .. n} <= c * (Upper_cap - Lower_cap), >= 0;

s.t. constraint1{t in 0 .. n-1}: sell[t] <= ((1-buy_or_sell[t]) * Upper_sell - sell_prev[t]) * restrict[t];
s.t. constraint2{t in 0 .. n-1}: sell[t] >= - sell_prev[t] * restrict[t];

s.t. constraint3{t in 0 .. n-1}: buy[t] <= (buy_or_sell[t] * Upper_buy - buy_prev[t]) * restrict[t];
s.t. constraint4{t in 0 .. n-1}: buy[t] >= - buy_prev[t] * restrict[t]; 

s.t. constraint5: cap[0] = cap_0;
s.t. constraint6{t in 0 .. n-1}: cap[t+1] = cap[t] + alpha * (buy[t] + buy_prev[t]) - (sell[t] + sell_prev[t]) / beta;
s.t. constraint7: cap[n] = cap_n;

s.t. constraint8: buy_cycles[0] = 0;
s.t. constraint9{t in 0 .. n-1}: buy_cycles[t+1] = buy_cycles[t] + alpha * (buy[t] + buy_prev[t]);

s.t. constraint10: sell_cycles[0] = 0;
s.t. constraint11{t in 0 .. n-1}: sell_cycles[t+1] = sell_cycles[t] + (sell[t] + sell_prev[t]) / beta;

maximize obj_fun: sum{t in 0 .. n-1} (price_bid[t] * sell[t] - price_ask[t] * buy[t]);

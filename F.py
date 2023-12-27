# %%
import requests
import re
import numpy as np
import time
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import matplotlib
import matplotlib.font_manager
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st
from IPython.display import display

# font setting
#!gdown 1lv0-HBUhnM0rg7rOWDYWPUp93WB5xwsM -O taipei_sans_tc_beta.ttf
matplotlib.font_manager.fontManager.addfont('taipei_sans_tc_beta.ttf')
matplotlib.rc('font', family = 'Taipei Sans TC Beta')

# %%


# %%
G = pd.read_csv('./sieux.csv', encoding='utf-8')
kaotian = pd.read_csv('./kaotian.csv', encoding='utf-8')

# 調整資料
# 增加AB的項目
G['AB'] = [re.findall(r'A|B', i) for i in G['韻母']]
G['AB'] = [i[0] if i != [] else '-' for i in G['AB']]
# 統一不同聲調的韻目
G['韻目'] = [re.sub(r'一|二|三|開|合|A|B', '', i) if i != '合' else '合' for i in G['韻母']]

# fillna
kaotian = kaotian.fillna('-')

# 合併閩南語字典與廣韻
D = pd.merge(G, kaotian, on='字', how='inner')

# %%
bun = D[D['文白音'] == '文']
b_siann = bun.groupby(['聲母', '閩南語聲母']).size().reset_index(name='字數')

# 使用 transform 計算比例並新增一列 '比例'
b_siann['比例'] = b_siann['字數'] / b_siann.groupby('聲母')['字數'].transform('sum')
#b_siann[b_siann['比例'] > 0.5].sort_values(by='比例', ascending=False)
b_siann = b_siann.sort_values(by='比例', ascending=False)
bun['temp'] = False

for i, row in b_siann.iterrows():
    s = row['聲母']
    ms = row['閩南語聲母']

    for j in list(bun[(bun['聲母'] == s) & (bun['閩南語聲母'] == ms)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['聲母'] == s) & (bun['閩南語聲母'] == ms) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']


b_siann = bun.groupby(['聲母', '閩南語聲母']).size().reset_index(name='字數')
b_siann['比例'] = b_siann['字數'] / b_siann.groupby('聲母')['字數'].transform('sum')
b_siann = b_siann.sort_values(by='比例', ascending=False)
b_siann['比例'] = round(b_siann['比例'], 2)
b_siann['例字'] = [list(bun[(bun['聲母'] == row['聲母']) & (bun['閩南語聲母'] == row['閩南語聲母'])]['字'])[0] for i, row in b_siann.iterrows()]
bg_siann = pd.DataFrame(b_siann.groupby(['聲母', '閩南語聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
x = [
    b_siann.sort_values('聲母').iloc[0:39]['聲母'],
    b_siann.sort_values('聲母').iloc[0:39]['閩南語聲母']
]
figs1 = go.Figure()
# 把資料分成上下兩張圖，不然會太擠
figs1.add_bar(x=x,y=b_siann.sort_values('聲母')[0:39]['比例'], text=b_siann.sort_values('聲母')[0:39]['例字']
            , textposition='outside', textfont=dict(size=9))

# 變更顏色、添加標題和座標軸名稱
figs1.update_layout(
    colorway=['#FFA15A', '#636EFA'],
    title='閩南語聲母對應比例 (上)',
    xaxis_title='聲母',
    yaxis_title='比例'
)

# 第一張圖

''''''

x = [
    b_siann.sort_values('聲母').iloc[40:79]['聲母'],
    b_siann.sort_values('聲母').iloc[40:79]['閩南語聲母']
]
figs2 = go.Figure()
figs2.add_bar(x=x,y=b_siann.sort_values('聲母')[40:79]['比例'], text=b_siann.sort_values('聲母')[40:79]['例字']
            , textposition='outside', textfont=dict(size=9))

# 變更顏色、添加標題和座標軸名稱
figs2.update_layout(
    colorway=['#FFA15A', '#636EFA'],
    title='閩南語聲母對應比例 (下)',
    xaxis_title='聲母',
    yaxis_title='比例'
)

# 第二張圖

# %%
l = [i for i in b_siann['聲母'] if (b_siann[b_siann['聲母'] == i]['閩南語聲母'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['聲母'] == i]['等'].unique()) != 1)]
bst0 = bun.query('聲母 in @l')
bst = bst0.groupby(['聲母', '等', '閩南語聲母']).size().reset_index(name='字數')
bst['比例'] = bst['字數'] / bst.groupby(['聲母', '等'])['字數'].transform('sum')

''''''

bst = bst.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in bst.iterrows():
    s = row['聲母']
    ms = row['閩南語聲母']
    t = row['等']

    for j in list(bun[(bun['聲母'] == s) & (bun['閩南語聲母'] == ms) & (bun['等'] == t)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['聲母'] == s) & (bun['閩南語聲母'] == ms) & (bun['等'] == t) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

bst0 = bun.query('聲母 in @l')
bst = bst0.groupby(['聲母', '等', '閩南語聲母']).size().reset_index(name='字數')
bst['比例'] = bst['字數'] / bst.groupby(['聲母', '等'])['字數'].transform('sum')
bst['比例'] = round(bst['比例'], 2)

''''''

for i in bst['聲母'].unique():
    tnum = len(bun[bun['聲母'] == i]['等'].unique())
    npstd = 0
    for j in bst[bst['聲母'] == i]['閩南語聲母'].unique():
        l = list(bst[(bst['聲母'] == i) & (bst['閩南語聲母'] == j)]['比例'])
        while len(l) < tnum:
            l.append(0)
        npstd += np.std(l)*(bst[(bst['聲母'] == i) & (bst['閩南語聲母'] == j)].shape[0] / bst[bst['聲母'] == i].shape[0])
    #print(i, npstd)
    bst.loc[bst['聲母'] == i,'temp'] = npstd
bst = bst[bst['temp'] > 0.2]
del bst['temp']

''''''

bst['例字'] = [list(bst0[(bst0['聲母'] == row['聲母']) & (bst0['閩南語聲母'] == row['閩南語聲母']) & (bst0['等'] == row['等'])]['字'])[0] for i, row in bst.iterrows()]
bgst = pd.DataFrame(bst.groupby(['聲母','等', '閩南語聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
bun = D[D['文白音'] == '文']
b_un = bun.groupby(['韻目', '閩南語韻母']).size().reset_index(name='字數')

# 使用 transform 計算比例並新增一列 '比例'
b_un['比例'] = b_un['字數'] / b_un.groupby('韻目')['字數'].transform('sum')
b_un = b_un.sort_values(by='比例', ascending=False)
bun['temp'] = False

for i, row in b_un.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']


b_un = bun.groupby(['韻目', '閩南語韻母']).size().reset_index(name='字數')
b_un['比例'] = b_un['字數'] / b_un.groupby('韻目')['字數'].transform('sum')
b_un = b_un.sort_values(by='比例', ascending=False)
b_un['比例'] = round(b_un['比例'], 2)
b_un['例字'] = [list(bun[(bun['韻目'] == row['韻目']) & (bun['閩南語韻母'] == row['閩南語韻母'])]['字'])[0] for i, row in b_un.iterrows()]
bg_un = pd.DataFrame(b_un.groupby(['韻目', '閩南語韻母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
x = [
    b_un.sort_values('韻目').iloc[0:47]['韻目'],
    b_un.sort_values('韻目').iloc[0:47]['閩南語韻母']
]
figu1 = go.Figure()
# 把資料分成三張圖，不然會太擠
figu1.add_bar(x=x,y=b_un.sort_values('韻目')[0:47]['比例'], text=b_un.sort_values('韻目')[0:47]['例字']
            , textposition='outside', textfont=dict(size=9))

# 變更顏色、添加標題和座標軸名稱
figu1.update_layout(
    colorway=['#D25350', '#636EFA'],
    title='閩南語韻母對應比例 (上)',
    xaxis_title='韻目',
    yaxis_title='比例'
)

# 第一張圖

''''''

x = [
    b_un.sort_values('韻目').iloc[48:96]['韻目'],
    b_un.sort_values('韻目').iloc[48:96]['閩南語韻母']
]
figu2 = go.Figure()
figu2.add_bar(x=x,y=b_un.sort_values('韻目')[48:96]['比例'], text=b_un.sort_values('韻目')[48:96]['例字']
            , textposition='outside', textfont=dict(size=9))

# 變更顏色、添加標題和座標軸名稱
figu2.update_layout(
    colorway=['#D25350', '#636EFA'],
    title='閩南語韻母對應比例 (中)',
    xaxis_title='韻目',
    yaxis_title='比例'
)

# 第二張圖

''''''

x = [
    b_un.sort_values('韻目').iloc[97:]['韻目'],
    b_un.sort_values('韻目').iloc[97:]['閩南語韻母']
]
figu3 = go.Figure()
figu3.add_bar(x=x,y=b_un.sort_values('韻目')[97:]['比例'], text=b_un.sort_values('韻目')[97:]['例字']
            , textposition='outside', textfont=dict(size=9))

# 變更顏色、添加標題和座標軸名稱
figu3.update_layout(
    colorway=['#D25350', '#636EFA'],
    title='閩南語韻母對應比例 (下)',
    xaxis_title='韻目',
    yaxis_title='比例'
)

# 第三張圖


# %%
l = [i for i in b_un['韻目'] if (b_un[b_un['韻目'] == i]['閩南語韻母'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['韻目'] == i]['呼'].unique()) != 1)]
buh0 = bun.query('韻目 in @l')
buh = buh0.groupby(['韻目', '呼', '閩南語韻母']).size().reset_index(name='字數')
buh['比例'] = buh['字數'] / buh.groupby(['韻目', '呼'])['字數'].transform('sum')
''''''

buh = buh.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in buh.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']
    h = row['呼']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['呼'] == h)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['呼'] == h) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

buh0 = bun.query('韻目 in @l')
buh = buh0.groupby(['韻目', '呼', '閩南語韻母']).size().reset_index(name='字數')
buh['比例'] = buh['字數'] / buh.groupby(['韻目', '呼'])['字數'].transform('sum')
buh['比例'] = round(buh['比例'], 2)

''''''

for i in buh['韻目'].unique():
    npstd = 0
    for j in buh[buh['韻目'] == i]['閩南語韻母'].unique():
        l = list(buh[(buh['韻目'] == i) & (buh['閩南語韻母'] == j)]['比例'])
        while len(l) < 2:
            l.append(0)
        npstd += np.std(l)*(buh[(buh['韻目'] == i) & (buh['閩南語韻母'] == j)].shape[0] / buh[buh['韻目'] == i].shape[0])
    print(i, npstd)
    buh.loc[buh['韻目'] == i, 'temp'] = npstd
buh = buh[buh['temp'] > 0.2]
del buh['temp']

''''''
buh['例字'] = [list(buh0[(buh0['韻目'] == row['韻目']) & (buh0['閩南語韻母'] == row['閩南語韻母']) & (buh0['呼'] == row['呼'])]['字'])[0] for i, row in buh.iterrows()]
bguh = pd.DataFrame(buh.groupby(['韻目','呼', '閩南語韻母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
l = [i for i in buh['韻目'] if (buh[(buh['韻目'] == i)]['比例'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['韻目'] == i]['等'].unique()) != 1)]
buth0 = bun.query('韻目 in @l')
buth = buth0.groupby(['韻目', '等', '呼', '閩南語韻母']).size().reset_index(name='字數')
buth['比例'] = buth['字數'] / buth.groupby(['韻目', '等', '呼'])['字數'].transform('sum')
''''''

buth = buth.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in buth.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']
    t = row['等']
    h = row['呼']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['呼'] == h) & (bun['等'] == t)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['呼'] == h) & (bun['等'] == t) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

buth0 = bun.query('韻目 in @l')
buth = buth0.groupby(['韻目', '等', '呼', '閩南語韻母']).size().reset_index(name='字數')
buth['比例'] = buth['字數'] / buth.groupby(['韻目', '等', '呼'])['字數'].transform('sum')
buth['比例'] = round(buth['比例'], 2)

''''''

for i in buth['韻目'].unique():
    tnum = len(bun[bun['韻目'] == i]['等'].unique())
    npstd = 0
    for j in buth[buth['韻目'] == i]['閩南語韻母'].unique():
        l = list(buth[(buth['韻目'] == i) & (buth['閩南語韻母'] == j)]['比例'])
        while len(l) < tnum:
            l.append(0)
        npstd += np.std(l)*(buth[(buth['韻目'] == i) & (buth['閩南語韻母'] == j)].shape[0] / buth[buth['韻目'] == i].shape[0])
    print(i, npstd)
    buth.loc[buth['韻目'] == i, 'temp'] = npstd
buth = buth[buth['temp'] > 0.2]
del buth['temp']

''''''
buth['例字'] = [list(buth0[(buth0['韻目'] == row['韻目']) & (buth0['閩南語韻母'] == row['閩南語韻母']) & (buth0['等'] == row['等']) & (buth0['呼'] == row['呼'])]['字'])[0] for i, row in buth.iterrows()]
bguth = pd.DataFrame(buth.groupby(['韻目','等', '呼', '閩南語韻母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
l = [i for i in buth['韻目'] if (buth[(buth['韻目'] == i)]['比例'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['韻目'] == i]['等'].unique()) != 1)]
buths0 = bun.query('韻目 in @l')
buths = buths0.groupby(['韻目', '等', '呼', '聲母', '閩南語韻母']).size().reset_index(name='字數')
buths['比例'] = buths['字數'] / buths.groupby(['韻目', '等', '呼', '閩南語韻母'])['字數'].transform('sum')
''''''

buths = buths.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in buths.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']
    t = row['等']
    h = row['呼']
    s = row['聲母']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['呼'] == h) & (bun['等'] == t) & (bun['聲母'] == s)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['呼'] == h) & (bun['等'] == t) & (bun['聲母'] == s) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

buths0 = bun.query('韻目 in @l')
buths = buths0.groupby(['韻目', '等', '呼', '聲母', '閩南語韻母']).size().reset_index(name='字數')
buths['比例'] = buths['字數'] / buths.groupby(['韻目', '等', '呼', '閩南語韻母'])['字數'].transform('sum')
buths['比例'] = round(buths['比例'], 2)

''''''

for i in buths['韻目'].unique():
    munum = len(bun[bun['韻目'] == i]['閩南語韻母'].unique())
    npstd = 0
    for j in buths[buths['韻目'] == i]['聲母'].unique():
        l = list(buths[(buths['韻目'] == i) & (buths['聲母'] == j)]['比例'])
        while len(l) < munum:
            l.append(0)
        npstd += np.std(l)*(buths[(buths['韻目'] == i) & (buths['聲母'] == j)].shape[0] / buths[buths['韻目'] == i].shape[0])
    print(i, npstd)
    buths.loc[buths['韻目'] == i, 'temp'] = npstd
buths = buths[buths['temp'] > 0.2]
del buths['temp']

''''''
buths['例字'] = [list(buths0[(buths0['韻目'] == row['韻目']) & (buths0['閩南語韻母'] == row['閩南語韻母']) & (buths0['等'] == row['等']) & (buths0['呼'] == row['呼']) & (buths0['聲母'] == row['聲母'])]['字'])[0] for i, row in buths.iterrows()]
bguth = pd.DataFrame(buths.groupby(['韻目','等', '呼', '閩南語韻母', '聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
l = [i for i in b_un['韻目'] if (b_un[(b_un['韻目'] == i)]['比例'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['韻目'] == i]['等'].unique()) != 1)]
but0 = bun.query('(韻目 in @l) & ~(韻目 in @buh["韻目"])')
but = but0.groupby(['韻目', '等', '閩南語韻母']).size().reset_index(name='字數')
but['比例'] = but['字數'] / but.groupby(['韻目', '等', '閩南語韻母'])['字數'].transform('sum')

''''''

but = but.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in but.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']
    t = row['等']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['等'] == t)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['等'] == t) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

but0 = bun.query('韻目 in @l & ~(韻目 in @buh["韻目"])')
but = but0.groupby(['韻目', '等', '閩南語韻母']).size().reset_index(name='字數')
but['比例'] = but['字數'] / but.groupby(['韻目', '等'])['字數'].transform('sum')
but['比例'] = round(but['比例'], 2)

''''''

for i in but['韻目'].unique():
    tnum = len(bun[bun['韻目'] == i]['等'].unique())
    npstd = 0
    for j in but[but['韻目'] == i]['閩南語韻母'].unique():
        l = list(but[(but['韻目'] == i) & (but['閩南語韻母'] == j)]['比例'])
        while len(l) < tnum:
            l.append(0)
        npstd += np.std(l)*(but[(but['韻目'] == i) & (but['閩南語韻母'] == j)].shape[0] / but[but['韻目'] == i].shape[0])
    print(i, npstd)
    but.loc[but['韻目'] == i, 'temp'] = npstd
but = but[but['temp'] > 0.2]
del but['temp']

''''''
but['例字'] = [list(but0[(but0['韻目'] == row['韻目']) & (but0['閩南語韻母'] == row['閩南語韻母']) & (but0['等'] == row['等'])]['字'])[0] for i, row in but.iterrows()]
bgut = pd.DataFrame(but.groupby(['韻目','等', '閩南語韻母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
l = [i for i in b_un['韻目'] if (but[(but['韻目'] == i)]['比例'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['韻目'] == i]['聲母'].unique()) != 1)]
buts0 = bun.query('(韻目 in @l) & (韻目 in @but["韻目"]) & ~(韻目 in @buh["韻目"])')
buts = buts0.groupby(['韻目', '等', '聲母', '閩南語韻母']).size().reset_index(name='字數')
buts['比例'] = buts.groupby(['韻目', '閩南語韻母', '等'])['字數'].transform('sum') / buts.groupby(['韻目', '等'])['字數'].transform('sum')

''''''

buts = buts.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in buts.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']
    t = row['等']
    s = row['聲母']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['等'] == t) & (bun['聲母'] == s)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['等'] == t) & (bun['聲母'] == s) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

buts0 = bun.query('韻目 in @l & (韻目 in @but["韻目"])  & ~(韻目 in @buh["韻目"])')
buts = buts0.groupby(['韻目', '等', '聲母', '閩南語韻母']).size().reset_index(name='字數')

buts['聲母'] = [list(buts0[(buts0['韻目'] == row['韻目']) & (buts0['閩南語韻母'] == row['閩南語韻母']) & (buts0['等'] == row['等'])]['聲母']) for i, row in buts.iterrows()]
def O(x):
    o = ''
    x = list(set(x))
    for i in list(x):
        o += str(i)
    return o
buts['聲母'] = buts['聲母'].apply(O)
buts = buts.drop_duplicates()
buts['比例'] = buts.groupby(['韻目', '閩南語韻母', '等'])['字數'].transform('sum') / buts.groupby(['韻目', '等'])['字數'].transform('sum')
buts['比例'] = round(buts['比例'], 2)

''''''

buts['例字'] = [list(buts0[(buts0['韻目'] == row['韻目']) & (buts0['閩南語韻母'] == row['閩南語韻母']) & (buts0['等'] == row['等'])]['字'])[0] for i, row in buts.iterrows()]
bguts = pd.DataFrame(buts.groupby(['韻目','等', '閩南語韻母', '聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
l = [i for i in b_un['韻目'] if (b_un[b_un['韻目'] == i]['閩南語韻母'].count() != 1)]
l = list(set(l))
l = [i for i in l if (len(bun[bun['韻目'] == i]['聲母'].unique()) != 1)]
bus0 = bun.query('(韻目 in @l) & ~(韻目 in @buh["韻目"]) & ~(韻目 in @buts["韻目"])')
bus = bus0.groupby(['韻目', '聲母', '閩南語韻母']).size().reset_index(name='字數')
bus['比例'] = bus.groupby(['韻目', '閩南語韻母'])['字數'].transform('sum') / bus.groupby(['韻目'])['字數'].transform('sum')

''''''

bus = bus.sort_values(by='比例', ascending=False)
bun['temp'] = False
for i, row in bus.iterrows():
    u = row['韻目']
    mu = row['閩南語韻母']
    s = row['聲母']

    for j in list(bun[(bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['聲母'] == s)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['韻目'] == u) & (bun['閩南語韻母'] == mu) & (bun['聲母'] == h) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']

bus0 = bun.query('(韻目 in @l) & ~(韻目 in @buh["韻目"]) & ~(韻目 in @buts["韻目"])')
bus = bus0.groupby(['韻目', '聲母', '閩南語韻母']).size().reset_index(name='字數')

bus['聲母'] = [list(bus0[(bus0['韻目'] == row['韻目']) & (bus0['閩南語韻母'] == row['閩南語韻母'])]['聲母']) for i, row in bus.iterrows()]
def O(x):
    o = ''
    x = list(set(x))
    for i in list(x):
        o += str(i)
    return o
bus['聲母'] = bus['聲母'].apply(O)
bus = bus.drop_duplicates()
bus['比例'] = bus.groupby(['韻目', '閩南語韻母'])['字數'].transform('sum') / bus.groupby(['韻目'])['字數'].transform('sum')
bus['比例'] = round(bus['比例'], 2)

bus['例字'] = [list(bus0[(bus0['韻目'] == row['韻目']) & (bus0['閩南語韻母'] == row['閩南語韻母'])]['字'])[0] for i, row in bus.iterrows()]
bgus = pd.DataFrame(bus.groupby(['韻目', '閩南語韻母', '聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))


# %%
BGUS = buts.query('~(韻目 in @bus["韻目"])')
BGUS = pd.concat([BGUS, bus],ignore_index=True)
BGUS = BGUS.fillna('-')

BGUS = pd.DataFrame(BGUS.groupby(['韻目','等', '閩南語韻母', '聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))

# %%
BGUN = b_un.query('~(韻目 in @buh["韻目"])')
BGUN = pd.concat([BGUN, buh],ignore_index=True)
BGUN = BGUN.query('~(韻目 in @buth["韻目"])')
BGUN = pd.concat([BGUN, buth],ignore_index=True)
BGUN = BGUN.query('~(韻目 in @but["韻目"])')
BGUN = pd.concat([BGUN, but],ignore_index=True)

BGUN = BGUN.fillna('-')
BGUN['比例'] = BGUN['比例'].replace(1,'-')

BGUN = pd.DataFrame(BGUN.groupby(['韻目','等', '呼', '閩南語韻母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))

# %%
BGSIANN = b_siann.query('~(聲母 in @bst["聲母"])')
BGSIANN = pd.concat([BGSIANN, bst],ignore_index=True)

BGSIANN = BGSIANN.fillna('-')
BGSIANN['比例'] = BGSIANN['比例'].replace(1,'-')

BGSIANN = pd.DataFrame(BGSIANN.groupby(['聲母','等', '閩南語聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))

# %%
bun = D[D['文白音'] == '文']
b_tiao = bun.groupby(['閩南語調', '調']).size().reset_index(name='字數')

# 使用 transform 計算比例並新增一列 '比例'
b_tiao['比例'] = b_tiao['字數'] / b_tiao.groupby('調')['字數'].transform('sum')
b_tiao = b_tiao.sort_values(by='比例', ascending=False)
bun['temp'] = False

for i, row in b_tiao.iterrows():
    t = row['調']
    mt = row['閩南語調']

    for j in list(bun[(bun['調'] == t) & (bun['閩南語調'] == mt)]['字']):
            if bun[bun['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                bun = bun[~((bun['字'] == j) & (~bun['temp']))]
            else:
                bun.loc[((bun['調'] == t) & (bun['閩南語調'] == mt) & (bun['字'] == j)),'temp'] = True
        
del bun['temp']


b_tiao = bun.groupby(['閩南語調', '調']).size().reset_index(name='字數')
b_tiao['比例'] = b_tiao['字數'] / b_tiao.groupby('閩南語調')['字數'].transform('sum')
b_tiao['比例'] = round(b_tiao['比例'], 2)
b_tiao = b_tiao.sort_values(by='比例', ascending=False)
b_tiao['例字'] = [list(bun[(bun['調'] == row['調']) & (bun['閩南語調'] == row['閩南語調'])]['字'])[0] for i, row in b_tiao.iterrows()]

bg_tiao = pd.DataFrame(b_tiao.groupby(['閩南語調', '調', '比例'])['例字'].apply(lambda x : list(x)[0]))

# %%
x = [
    b_tiao.sort_values('閩南語調')['閩南語調'],
    b_tiao.sort_values('閩南語調')['調']
]
figt = go.Figure()
figt.add_bar(x=x,y=b_tiao.sort_values('閩南語調')['比例'], text=b_tiao.sort_values('閩南語調')['例字']
            , textposition='outside', textfont=dict(size=9))

# 變更顏色、添加標題和座標軸名稱
figt.update_layout(
    colorway=['#5FA15A', '#C36EFA'],
    title='閩南語調對應的平上去入',
    xaxis_title='第N調',
    yaxis_title='比例'
)



# %%

# %%
# 定義Streamlit應用程序的標題
st.title("中古音對應閩南語文音查詢系統")

# 添加輸入框，允許使用者輸入項目
st.markdown('輸入1: 中古聲母與閩南語聲母對應表')
st.markdown('輸入2: 中古聲母與閩南語聲母對應關係圖')
st.markdown('輸入3: 中古韻母與閩南語韻母對應表')
st.markdown('輸入4: 中古韻母與閩南語韻母對應關係圖')
st.markdown('輸入5: 中古韻母與閩南語韻母歧音對應聲母')
st.markdown('輸入6: 中古聲調與閩南語聲調對應關係圖')
user_input = st.text_area("請輸入要查詢的項目，以逗號分隔","")

# 定義生成圖表的函數
def generator(text):
    for i in text.split(','):
        if i == '1':
            st.markdown(BGSIANN.to_html(classes='dataframe'), unsafe_allow_html=True)
        elif i == '2':
            st.write(figs1, unsafe_allow_html=True)
            st.write(figs2, unsafe_allow_html=True)
        elif i == '3':
            st.markdown(BGUN.to_html(classes='dataframe'), unsafe_allow_html=True)
        elif i == '4':
            st.write(figu1, unsafe_allow_html=True)
            st.write(figu2, unsafe_allow_html=True)
            st.write(figu3, unsafe_allow_html=True)
        elif i == '5':
            st.markdown(BGUS.to_html(classes='dataframe'), unsafe_allow_html=True)
        elif i == '6':
            st.write(figt, unsafe_allow_html=True)
        else:
            st.write('輸入錯誤')

# 添加生成的按鈕
if st.button("查詢"):
    if user_input:
        generator(user_input)
    else:
        st.warning("請先輸入")



# %% [markdown]
# # 中古音對應閩南語音查詢系統
# ### 後續程式

# %% [markdown]
# 以下要作的事情，就是想辦法以最工整的方式歸納出<<廣韻>>的聲韻與閩南語讀音的對應關係，作出精簡的圖表，並且最終作以streamlit的方式呈現。

# %% [markdown]
# ### Import

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

# font setting
#!gdown 1lv0-HBUhnM0rg7rOWDYWPUp93WB5xwsM -O taipei_sans_tc_beta.ttf
matplotlib.font_manager.fontManager.addfont('taipei_sans_tc_beta.ttf')
matplotlib.rc('font', family = 'Taipei Sans TC Beta')

# %% [markdown]
# ### ... 這部分就是重複"資料提取"當中的內容，可跳過

# %% [markdown]
# ### 讀取先前提取的資料

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
D.head(20)

# %% [markdown]
# ### 處理聲母

# %% [markdown]
# #### 基本對照

# %%
def s1():
    im = D[D['文白音'] == bp]
    siann = im.groupby(['聲母', '閩南語聲母']).size().reset_index(name='字數')

    # 使用 transform 計算比例並新增一列 '比例'
    siann['比例'] = siann['字數'] / siann.groupby('聲母')['字數'].transform('sum')
    #siann[siann['比例'] > 0.5].sort_values(by='比例', ascending=False)
    siann = siann.sort_values(by='比例', ascending=False)

    # 剛才已經由高到低排好中古聲母與閩南語各相應關係的比例，愈前面的比例愈大，代表愈有可能是對應的聲母
    # 廣韻裡面的破音字多到嚇死人，平均每4個字就有1個是破音字。那些頻率低的相應關係可能只是沒有對到相應的讀音
    # 所以我們從最前面開始，依次將該聲母與所對應最合理的閩南語聲母標記為 True，並將其餘不同的讀音標記為 False，然後刪除
    im['temp'] = False

    for i, row in siann.iterrows():
        s = row['聲母']
        ms = row['閩南語聲母']

        for j in list(im[(im['聲母'] == s) & (im['閩南語聲母'] == ms)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['聲母'] == s) & (im['閩南語聲母'] == ms) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 破音字清乾淨之後，中古聲母與閩南語各相應關係應該會有不小改變，所以我們再重新計算一次比例
    siann = im.groupby(['聲母', '閩南語聲母']).size().reset_index(name='字數')
    siann['比例'] = siann['字數'] / siann.groupby('聲母')['字數'].transform('sum')
    siann = siann.sort_values(by='比例', ascending=False)
    siann['比例'] = round(siann['比例'], 2)

    # 每個對應關係中，挑出一個例字，能夠理解得更清楚
    siann['例字'] = [list(im[(im['聲母'] == row['聲母']) & (im['閩南語聲母'] == row['閩南語聲母'])]['字'])[0] for i, row in siann.iterrows()]
    return im, siann

# %% [markdown]
# #### 作圖

# %%
# 由於似乎沒找到甚麼有效的方法可以畫出三層以上的群組長條圖，所以以下只有最基本的中古音與閩南語聲韻調的對應關係會以圖呈現，等呼的差異只能以表格呈現
# 每張圖的長條數量有限，長條太多字會跑不出來，所以我們將資料分成數張圖呈現
def sfig(siann):
    i = 0 # 長條數量修正值
    j =0 # 圖片編號
    per = 37 # 每張圖的長條數量
    now = 0 # 現在的長條位置
    order = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九']
    all_figs = []
    while now < siann.shape[0]:
        # 不能讓圖片的長條數量超過資料的長條數量，不然會壞掉
        if now+per-1 >= siann.shape[0]:
            # 讓最後一張圖的累計長條數量等於資料的長條數量
            i = siann.shape[0]-now-per
        elif now+per == siann.shape[0]:
            i = 0
        else:
            # 不要讓同一個項目拆成兩張圖
            while siann.sort_values('聲母').iloc[now+per+i-1]['聲母'] == siann.sort_values('聲母').iloc[now+per+i]['聲母']:
                i += 1
                if now+per+i-1 == siann.shape[0]:
                    break
        x = [
            siann.sort_values('聲母').iloc[now:now+per+i]['聲母'],
            siann.sort_values('聲母').iloc[now:now+per+i]['閩南語聲母']
        ]
        figs = go.Figure()
        figs.add_bar(x=x,y=siann.sort_values('聲母')[now:now+per+i]['比例'], text=siann.sort_values('聲母')[now:now+per+i]['例字']
                    , textposition='outside', textfont=dict(size=9))

        # 變更顏色、添加標題和座標軸名稱
        figs.update_layout(
            colorway=['#FFA15A', '#636EFA'],
            title=f'閩南語{bp}音聲母對應比例 ({order[j]})',
            xaxis_title='聲母',
            yaxis_title='比例'
        )    
        # 把所有圖存在一起
        all_figs.append(figs)
        now += per+i
        i = 0
        j += 1
        if now >= siann.shape[0]:
            break
    return all_figs

# %% [markdown]
# #### 細部對照

# %% [markdown]
# ##### 分析聲母與等

# %%
# 找出中古聲母對應閩南語聲母有分歧的聲母，分析看看是為甚麼
# 先假設閩南語聲母的分歧是因為等的差異，所以我們先找出不同的等
def s2(im, siann):
    l = [i for i in siann['聲母'] if (siann[siann['聲母'] == i]['閩南語聲母'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['聲母'] == i]['等'].unique()) != 1)]
    st0 = im.query('聲母 in @l')
    st_ = st0.groupby(['聲母', '等', '閩南語聲母']).size().reset_index(name='字數')
    st_['比例'] = st_['字數'] / st_.groupby(['聲母', '等'])['字數'].transform('sum')

    ''''''
    # 消除破音字，跟之前一樣
    st_ = st_.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in st_.iterrows():
        s = row['聲母']
        ms = row['閩南語聲母']
        t = row['等']

        for j in list(im[(im['聲母'] == s) & (im['閩南語聲母'] == ms) & (im['等'] == t)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['聲母'] == s) & (im['閩南語聲母'] == ms) & (im['等'] == t) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    st0 = im.query('聲母 in @l')
    st_ = st0.groupby(['聲母', '等', '閩南語聲母']).size().reset_index(name='字數')
    st_['比例'] = st_['字數'] / st_.groupby(['聲母', '等'])['字數'].transform('sum')
    st_['比例'] = round(st_['比例'], 2)

    ''''''
    # 聲母的分歧不見得都與等相關，因此比較一個字對應到同樣的閩南語聲母，不同等的標準差，並將標準差大於0.2才的聲母挑出來，來粗略鑑驗其相關性
    st_['temp'] = 0
    for i in st_['聲母'].unique():
        tnum = len(im[im['聲母'] == i]['等'].unique())
        nstd = 0
        for j in st_[st_['聲母'] == i]['閩南語聲母'].unique():
            l = list(st_[(st_['聲母'] == i) & (st_['閩南語聲母'] == j)]['比例'])
            while len(l) < tnum:
                l.append(0)
            nstd += np.std(l)*(st_[(st_['聲母'] == i) & (st_['閩南語聲母'] == j)].shape[0] / st_[st_['聲母'] == i].shape[0])
        #print(i, nstd)
        st_.loc[st_['聲母'] == i,'temp'] = nstd
    # 若標準差未大於0.2，則認為分歧不夠，恐怕不是等的問題，刪除。以下皆以標準差大於0.2為準
    st_ = st_[st_['temp'] > 0.2]
    del st_['temp']

    ''''''
    # 例字
    st_['例字'] = [list(st0[(st0['聲母'] == row['聲母']) & (st0['閩南語聲母'] == row['閩南語聲母']) & (st0['等'] == row['等'])]['字'])[0] for i, row in st_.iterrows()]
    return st_

# %% [markdown]
# ### 處理韻母

# %% [markdown]
# #### 基本對照

# %%
def u1():
    im = D[D['文白音'] == bp]
    un = im.groupby(['韻目', '閩南語韻母']).size().reset_index(name='字數')

    # 使用 transform 計算比例並新增一列 '比例'
    un['比例'] = un['字數'] / un.groupby('韻目')['字數'].transform('sum')
    un = un.sort_values(by='比例', ascending=False)
    im['temp'] = False

    # 消除破音字
    for i, row in un.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    un = im.groupby(['韻目', '閩南語韻母']).size().reset_index(name='字數')
    un['比例'] = un['字數'] / un.groupby('韻目')['字數'].transform('sum')
    un = un.sort_values(by='比例', ascending=False)
    un['比例'] = round(un['比例'], 2)

    # 例字
    un['例字'] = [list(im[(im['韻目'] == row['韻目']) & (im['閩南語韻母'] == row['閩南語韻母'])]['字'])[0] for i, row in un.iterrows()]
    return im, un

# %% [markdown]
# #### 作圖

# %%
# 跟之前sfig()的作法一樣
def ufig(un):
    i = 0
    j =0
    per = 37
    now = 0
    order = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九']
    all_figu = []
    while now < un.shape[0]:
        if now+per-1 >= un.shape[0]:
            i = un.shape[0]-now-per
        elif now+per == un.shape[0]:
            i = 0
        else:
            while un.sort_values('韻目').iloc[now+per+i-1]['韻目'] == un.sort_values('韻目').iloc[now+per+i]['韻目']:
                i += 1
                if now+per+i-1 == un.shape[0]:
                    break
        x = [
            un.sort_values('韻目').iloc[now:now+per+i]['韻目'],
            un.sort_values('韻目').iloc[now:now+per+i]['閩南語韻母']
        ]
        figu = go.Figure()
        figu.add_bar(x=x,y=un.sort_values('韻目')[now:now+per+i]['比例'], text=un.sort_values('韻目')[now:now+per+i]['例字']
                    , textposition='outside', textfont=dict(size=9))

        # 變更顏色、添加標題和座標軸名稱
        figu.update_layout(
            colorway=['#D25350', '#636EFA'],
            title=f'閩南語{bp}音韻母對應比例 ({order[j]})',
            xaxis_title='韻目',
            yaxis_title='比例'
        )    
        all_figu.append(figu)
        now += per+i
        i = 0
        j += 1
        if now >= un.shape[0]:
            break
    return all_figu

# %% [markdown]
# #### 細部對照

# %% [markdown]
# ##### 分析韻母與呼

# %%
# 找出分歧韻母，分析開合口呼的因素
def u2(im, un):
    l = [i for i in un['韻目'] if (un[un['韻目'] == i]['閩南語韻母'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['呼'].unique()) != 1)]
    uh0 = im.query('韻目 in @l')
    uh = uh0.groupby(['韻目', '呼', '閩南語韻母']).size().reset_index(name='字數')
    uh['比例'] = uh['字數'] / uh.groupby(['韻目', '呼'])['字數'].transform('sum')
    
    ''''''
    # 消除破音字
    uh = uh.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in uh.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        h = row['呼']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    uh0 = im.query('韻目 in @l')
    uh = uh0.groupby(['韻目', '呼', '閩南語韻母']).size().reset_index(name='字數')
    uh['比例'] = uh['字數'] / uh.groupby(['韻目', '呼'])['字數'].transform('sum')
    uh['比例'] = round(uh['比例'], 2)

    ''''''

    # 鑑驗相關性
    uh['temp'] = 0
    for i in uh['韻目'].unique():
        nstd = 0
        for j in uh[uh['韻目'] == i]['閩南語韻母'].unique():
            l = list(uh[(uh['韻目'] == i) & (uh['閩南語韻母'] == j)]['比例'])
            while len(l) < 2:
                l.append(0)
            nstd += np.std(l)*(uh[(uh['韻目'] == i) & (uh['閩南語韻母'] == j)].shape[0] / uh[uh['韻目'] == i].shape[0])
        print(i, nstd)
        uh.loc[uh['韻目'] == i, 'temp'] = nstd
    uh = uh[uh['temp'] > 0.2]
    del uh['temp']

    ''''''
    # 例字
    uh['例字'] = [list(uh0[(uh0['韻目'] == row['韻目']) & (uh0['閩南語韻母'] == row['閩南語韻母']) & (uh0['呼'] == row['呼'])]['字'])[0] for i, row in uh.iterrows()]
    return uh

# %% [markdown]
# ##### 分析韻母與呼、等

# %%
# 找出分析開合口呼後還有分歧的韻母，分析等的因素
def u3(im, uh):
    l = [i for i in uh['韻目'] if (uh[(uh['韻目'] == i)]['比例'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['等'].unique()) != 1)]
    uth0 = im.query('韻目 in @l')
    uth = uth0.groupby(['韻目', '等', '呼', '閩南語韻母']).size().reset_index(name='字數')
    uth['比例'] = uth['字數'] / uth.groupby(['韻目', '等', '呼'])['字數'].transform('sum')
    ''''''

    # 消除破音字
    uth = uth.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in uth.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        t = row['等']
        h = row['呼']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['等'] == t)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['等'] == t) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    uth0 = im.query('韻目 in @l')
    uth = uth0.groupby(['韻目', '等', '呼', '閩南語韻母']).size().reset_index(name='字數')
    uth['比例'] = uth['字數'] / uth.groupby(['韻目', '等', '呼'])['字數'].transform('sum')
    uth['比例'] = round(uth['比例'], 2)

    ''''''

    # 鑑驗相關性
    uth['temp'] = 0
    for i in uth['韻目'].unique():
        tnum = len(im[im['韻目'] == i]['等'].unique())
        nstd = 0
        for j in uth[uth['韻目'] == i]['閩南語韻母'].unique():
            l = list(uth[(uth['韻目'] == i) & (uth['閩南語韻母'] == j)]['比例'])
            while len(l) < tnum:
                l.append(0)
            nstd += np.std(l)*(uth[(uth['韻目'] == i) & (uth['閩南語韻母'] == j)].shape[0] / uth[uth['韻目'] == i].shape[0])
        print(i, nstd)
        uth.loc[uth['韻目'] == i, 'temp'] = nstd
    uth = uth[uth['temp'] > 0.2]
    del uth['temp']

    ''''''
    # 例字
    uth['例字'] = [list(uth0[(uth0['韻目'] == row['韻目']) & (uth0['閩南語韻母'] == row['閩南語韻母']) & (uth0['等'] == row['等']) & (uth0['呼'] == row['呼'])]['字'])[0] for i, row in uth.iterrows()]
    return uth

# %% [markdown]
# ##### 分析韻母、等、呼之對應聲母

# %%
# 找出分析等呼後還有分歧的韻母，分析聲母的因素
def u4(im, uth):
    l = [i for i in uth['韻目'] if (uth[(uth['韻目'] == i)]['比例'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['等'].unique()) != 1)]
    uths0 = im.query('韻目 in @l')
    uths = uths0.groupby(['韻目', '等', '呼', '聲母', '閩南語韻母']).size().reset_index(name='字數')
    uths['比例'] = uths['字數'] / uths.groupby(['韻目', '等', '呼', '閩南語韻母'])['字數'].transform('sum')

    ''''''
    # 消除破音字
    uths = uths.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in uths.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        t = row['等']
        h = row['呼']
        s = row['聲母']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['等'] == t) & (im['聲母'] == s)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['等'] == t) & (im['聲母'] == s) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    uths0 = im.query('韻目 in @l')
    uths = uths0.groupby(['韻目', '等', '呼', '聲母', '閩南語韻母']).size().reset_index(name='字數')

    # 這裡在做的事是將同一個韻目、閩南語韻母組合對應的聲母合併
    # 先是把聲母組用list統整起來，套到每一個字的聲母欄位
    uths['聲母'] = [list(uths0[(uths0['韻目'] == row['韻目']) & (uths0['閩南語韻母'] == row['閩南語韻母']) & (uths0['呼'] == row['呼']) & (uths0['等'] == row['等'])]['聲母']) for i, row in uths.iterrows()]
    # 接著要把list裡的聲母拆成一個字串
    def O(x):
        o = ''
        x = list(set(x))
        for i in list(x):
            o += str(i)
        return o
    uths['聲母'] = uths['聲母'].apply(O)
    uths = uths.drop_duplicates()
    # 重新計算比例
    uths['比例'] = uths.groupby(['韻目', '閩南語韻母','呼', '等'])['字數'].transform('sum') / uths.groupby(['韻目','呼', '等'])['字數'].transform('sum')
    uths['比例'] = round(uths['比例'], 2)
    
    ''''''
    # 例字
    uths['例字'] = [list(uths0[(uths0['韻目'] == row['韻目']) & (uths0['閩南語韻母'] == row['閩南語韻母']) & (uths0['等'] == row['等']) & (uths0['呼'] == row['呼'])]['字'])[0] for i, row in uths.iterrows()]
    # 沒有分歧的部分挑出來
    uths = uths[uths['比例'] != 1]
    return uths

# %% [markdown]
# ##### 分析韻母與等

# %%
# 找出分析與呼無關的韻母，分析等的因素
def u5(im, un, uh):
    l = [i for i in un['韻目'] if (un[(un['韻目'] == i)]['比例'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['等'].unique()) != 1)]
    ut0 = im.query('(韻目 in @l) & ~(韻目 in @uh["韻目"])')
    ut = ut0.groupby(['韻目', '等', '閩南語韻母']).size().reset_index(name='字數')
    ut['比例'] = ut['字數'] / ut.groupby(['韻目', '等', '閩南語韻母'])['字數'].transform('sum')

    ''''''
    # 消除破音字
    ut = ut.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in ut.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        t = row['等']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['等'] == t)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['等'] == t) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    ut0 = im.query('韻目 in @l & ~(韻目 in @uh["韻目"])')
    ut = ut0.groupby(['韻目', '等', '閩南語韻母']).size().reset_index(name='字數')
    ut['比例'] = ut['字數'] / ut.groupby(['韻目', '等'])['字數'].transform('sum')
    ut['比例'] = round(ut['比例'], 2)

    ''''''
    # 鑑驗相關性
    ut['temp'] = 0
    for i in ut['韻目'].unique():
        tnum = len(im[im['韻目'] == i]['等'].unique())
        nstd = 0
        for j in ut[ut['韻目'] == i]['閩南語韻母'].unique():
            l = list(ut[(ut['韻目'] == i) & (ut['閩南語韻母'] == j)]['比例'])
            while len(l) < tnum:
                l.append(0)
            nstd += np.std(l)*(ut[(ut['韻目'] == i) & (ut['閩南語韻母'] == j)].shape[0] / ut[ut['韻目'] == i].shape[0])
        print(i, nstd)
        ut.loc[ut['韻目'] == i, 'temp'] = nstd
    ut = ut[ut['temp'] > 0.2]
    del ut['temp']

    ''''''
    # 例字
    ut['例字'] = [list(ut0[(ut0['韻目'] == row['韻目']) & (ut0['閩南語韻母'] == row['閩南語韻母']) & (ut0['等'] == row['等'])]['字'])[0] for i, row in ut.iterrows()]
    return ut

# %% [markdown]
# ##### 分析韻母與呼之對應聲母

# %%
# 找出分析呼後還有分歧且與等無關的韻母，看看其對應的聲母有哪些
def u6(im, un, uh, uth, ut):
    l = [i for i in un['韻目'] if (uh[(uh['韻目'] == i)]['比例'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['聲母'].unique()) != 1)]
    uhs0 = im.query('(韻目 in @l) & (韻目 in @uh["韻目"]) & ~(韻目 in @uth["韻目"]) & ~(韻目 in @ut["韻目"])')
    uhs = uhs0.groupby(['韻目', '呼', '聲母', '閩南語韻母']).size().reset_index(name='字數')
    uhs['比例'] = uhs.groupby(['韻目', '閩南語韻母', '呼'])['字數'].transform('sum') / uhs.groupby(['韻目', '呼'])['字數'].transform('sum')

    ''''''

    # 消除破音字
    uhs = uhs.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in uhs.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        h = row['呼']
        s = row['聲母']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['聲母'] == s)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['呼'] == h) & (im['聲母'] == s) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    uhs0 = im.query('(韻目 in @l) & (韻目 in @uh["韻目"]) & ~(韻目 in @uth["韻目"]) & ~(韻目 in @ut["韻目"])')
    uhs = uhs0.groupby(['韻目', '呼', '聲母', '閩南語韻母']).size().reset_index(name='字數')

    # 統整聲母
    uhs['聲母'] = [list(uhs0[(uhs0['韻目'] == row['韻目']) & (uhs0['閩南語韻母'] == row['閩南語韻母']) & (uhs0['呼'] == row['呼'])]['聲母']) for i, row in uhs.iterrows()]
    # 把list拆成str
    def O(x):
        o = ''
        x = list(set(x))
        for i in list(x):
            o += str(i)
        return o
    uhs['聲母'] = uhs['聲母'].apply(O)
    uhs = uhs.drop_duplicates()
    # 重新計算比例
    uhs['比例'] = uhs.groupby(['韻目', '閩南語韻母', '呼'])['字數'].transform('sum') / uhs.groupby(['韻目', '呼'])['字數'].transform('sum')
    uhs['比例'] = round(uhs['比例'], 2)

    ''''''

    # 例字
    uhs['例字'] = [list(uhs0[(uhs0['韻目'] == row['韻目']) & (uhs0['閩南語韻母'] == row['閩南語韻母']) & (uhs0['呼'] == row['呼'])]['字'])[0] for i, row in uhs.iterrows()]
    # 沒有分歧的部分挑出來
    uhs = uhs[uhs['比例'] != 1]
    guhs = pd.DataFrame(uhs.groupby(['韻目','呼', '閩南語韻母', '聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))
    return uhs

# %% [markdown]
# ##### 分析韻母與等之對應聲母

# %%
# 找出分析等後還有分歧且與呼無關的韻母，看看其對應的聲母有哪些
def u7(im, un, ut, uh):
    l = [i for i in un['韻目'] if (ut[(ut['韻目'] == i)]['比例'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['聲母'].unique()) != 1)]
    uts0 = im.query('(韻目 in @l) & (韻目 in @ut["韻目"]) & ~(韻目 in @uh["韻目"])')
    uts = uts0.groupby(['韻目', '等', '聲母', '閩南語韻母']).size().reset_index(name='字數')
    uts['比例'] = uts.groupby(['韻目', '閩南語韻母', '等'])['字數'].transform('sum') / uts.groupby(['韻目', '等'])['字數'].transform('sum')

    ''''''
    # 消除破音字
    uts = uts.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in uts.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        t = row['等']
        s = row['聲母']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['等'] == t) & (im['聲母'] == s)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['等'] == t) & (im['聲母'] == s) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    uts0 = im.query('韻目 in @l & (韻目 in @ut["韻目"])  & ~(韻目 in @uh["韻目"])')
    uts = uts0.groupby(['韻目', '等', '聲母', '閩南語韻母']).size().reset_index(name='字數')

    # 統整聲母
    uts['聲母'] = [list(uts0[(uts0['韻目'] == row['韻目']) & (uts0['閩南語韻母'] == row['閩南語韻母']) & (uts0['等'] == row['等'])]['聲母']) for i, row in uts.iterrows()]
    # 把list拆成str
    def O(x):
        o = ''
        x = list(set(x))
        for i in list(x):
            o += str(i)
        return o
    uts['聲母'] = uts['聲母'].apply(O)
    uts = uts.drop_duplicates()
    # 重新計算比例
    uts['比例'] = uts.groupby(['韻目', '閩南語韻母', '等'])['字數'].transform('sum') / uts.groupby(['韻目', '等'])['字數'].transform('sum')
    uts['比例'] = round(uts['比例'], 2)

    ''''''
    # 例字
    uts['例字'] = [list(uts0[(uts0['韻目'] == row['韻目']) & (uts0['閩南語韻母'] == row['閩南語韻母']) & (uts0['等'] == row['等'])]['字'])[0] for i, row in uts.iterrows()]
    # 沒有分歧的部分挑出來
    uts = uts[uts['比例'] != 1]
    return uts

# %% [markdown]
# ##### 分析韻母之對應聲母

# %%
# 找出有分歧且與等呼無關的韻母，看看其對應的聲母有哪些
def u8(im, un, uh, uts):
    l = [i for i in un['韻目'] if (un[un['韻目'] == i]['閩南語韻母'].count() != 1)]
    l = list(set(l))
    l = [i for i in l if (len(im[im['韻目'] == i]['聲母'].unique()) != 1)]
    us0 = im.query('(韻目 in @l) & ~(韻目 in @uh["韻目"]) & ~(韻目 in @uts["韻目"])')
    us = us0.groupby(['韻目', '聲母', '閩南語韻母']).size().reset_index(name='字數')
    us['比例'] = us.groupby(['韻目', '閩南語韻母'])['字數'].transform('sum') / us.groupby(['韻目'])['字數'].transform('sum')

    ''''''
    # 消除破音字
    us = us.sort_values(by='比例', ascending=False)
    im['temp'] = False
    for i, row in us.iterrows():
        u = row['韻目']
        mu = row['閩南語韻母']
        s = row['聲母']

        for j in list(im[(im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['聲母'] == s)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['韻目'] == u) & (im['閩南語韻母'] == mu) & (im['聲母'] == s) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    us0 = im.query('(韻目 in @l) & ~(韻目 in @uh["韻目"]) & ~(韻目 in @uts["韻目"])')
    us = us0.groupby(['韻目', '聲母', '閩南語韻母']).size().reset_index(name='字數')

    # 統整聲母
    us['聲母'] = [list(us0[(us0['韻目'] == row['韻目']) & (us0['閩南語韻母'] == row['閩南語韻母'])]['聲母']) for i, row in us.iterrows()]
    # 把list拆成str
    def O(x):
        o = ''
        x = list(set(x))
        for i in list(x):
            o += str(i)
        return o
    us['聲母'] = us['聲母'].apply(O)
    us = us.drop_duplicates()
    # 重新計算比例
    us['比例'] = us.groupby(['韻目', '閩南語韻母'])['字數'].transform('sum') / us.groupby(['韻目'])['字數'].transform('sum')
    us['比例'] = round(us['比例'], 2)

    ''''''
    # 例字
    us['例字'] = [list(us0[(us0['韻目'] == row['韻目']) & (us0['閩南語韻母'] == row['閩南語韻母'])]['字'])[0] for i, row in us.iterrows()]
    return us

# %% [markdown]
# ### 統整

# %%
# 彙整所有的歧音與其聲母的對應關係
def usdf(us, uts, uths, uhs):
    GUS = us.query('~(韻目 in @uts["韻目"])')
    GUS = pd.concat([GUS, uts],ignore_index=True)
    GUS = GUS.query('~(韻目 in @uths["韻目"])')
    GUS = pd.concat([GUS, uths],ignore_index=True)
    GUS = GUS.query('~(韻目 in @uhs["韻目"])')
    GUS = pd.concat([GUS, uhs],ignore_index=True)
    # 以下的原則是這樣：沒有區別就不需要寫出屬性，所以空出來的位置都可以'-'替代
    GUS = GUS.fillna('-')

    GUS = pd.DataFrame(GUS.groupby(['韻目','等','呼', '閩南語韻母', '聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))
    return GUS

# %%
# 彙整所有的韻母對應關係
def udf(un, uh, uth, ut):
    GUN = un.query('~(韻目 in @uh["韻目"])')
    GUN = pd.concat([GUN, uh],ignore_index=True)
    GUN = GUN.query('~(韻目 in @uth["韻目"])')
    GUN = pd.concat([GUN, uth],ignore_index=True)
    GUN = GUN.query('~(韻目 in @ut["韻目"])')
    GUN = pd.concat([GUN, ut],ignore_index=True)

    GUN = GUN.fillna('-')
    # 比例=1的都是沒有歧異的，所以可以用'-'替代
    GUN['比例'] = GUN['比例'].replace(1,'-')

    GUN = pd.DataFrame(GUN.groupby(['韻目','等', '呼', '閩南語韻母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))
    return GUN

# %%
# 彙整所有的聲母對應關係
def sdf(siann, st_):
    GSIANN = siann.query('~(聲母 in @st_["聲母"])')
    GSIANN = pd.concat([GSIANN, st_],ignore_index=True)

    GSIANN = GSIANN.fillna('-')
    GSIANN['比例'] = GSIANN['比例'].replace(1,'-')

    GSIANN = pd.DataFrame(GSIANN.groupby(['聲母','等', '閩南語聲母'])[['比例', '例字']].apply(lambda x: x.iloc[0]))
    return GSIANN

# %% [markdown]
# ### 處理聲調

# %%
def tfig():
    im = D[D['文白音'] == bp]
    tiao = im.groupby(['閩南語調', '調']).size().reset_index(name='字數')

    # 使用 transform 計算比例並新增一列 '比例'
    tiao['比例'] = tiao['字數'] / tiao.groupby('調')['字數'].transform('sum')
    tiao = tiao.sort_values(by='比例', ascending=False)
    im['temp'] = False

    # 消除破音字
    for i, row in tiao.iterrows():
        t = row['調']
        mt = row['閩南語調']

        for j in list(im[(im['調'] == t) & (im['閩南語調'] == mt)]['字']):
                if im[im['字'] == j].sort_values(by='temp', ascending=False)['temp'].reset_index().loc[0,'temp']:
                    im = im[~((im['字'] == j) & (~im['temp']))]
                else:
                    im.loc[((im['調'] == t) & (im['閩南語調'] == mt) & (im['字'] == j)),'temp'] = True
            
    del im['temp']

    # 重新計算比例
    tiao = im.groupby(['閩南語調', '調']).size().reset_index(name='字數')
    tiao['比例'] = tiao['字數'] / tiao.groupby('閩南語調')['字數'].transform('sum')
    tiao['比例'] = round(tiao['比例'], 2)
    tiao = tiao.sort_values(by='比例', ascending=False)

    # 例字
    tiao['例字'] = [list(im[(im['調'] == row['調']) & (im['閩南語調'] == row['閩南語調'])]['字'])[0] for i, row in tiao.iterrows()]


    # %%
    x = [
        tiao.sort_values('閩南語調')['閩南語調'],
        tiao.sort_values('閩南語調')['調']
    ]
    figt = go.Figure()
    figt.add_bar(x=x,y=tiao.sort_values('閩南語調')['比例'], text=tiao.sort_values('閩南語調')['例字']
                , textposition='outside', textfont=dict(size=9))

    # 變更顏色、添加標題和座標軸名稱
    figt.update_layout(
        colorway=['#5FA15A', '#C36EFA'],
        title=f'閩南語{bp}音聲調對應的平上去入',
        xaxis_title='第N調',
        yaxis_title='比例'
    )
    return figt

# %% [markdown]
# ### 在Streamlit上執行

# %%
# 結果要用Streamlit的形式呈現
# 定義Streamlit應用程序的標題
st.title("中古音對應閩南語音查詢系統")

# 添加下拉式選單，選擇查詢文音、白音、替字、或歸屬不明的字(-)
bp = st.selectbox("請選擇查詢文音或白音", ["文", "白", "-", "替"])
st.write("請耐心等待，系統有點慢 (有些單項可能就要四分鐘左右)")

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
            im, siann = s1()
            st_ = s2(im, siann)
            st.markdown(sdf(siann, st_).to_html(classes='dataframe'), unsafe_allow_html=True)
        elif i == '2':
            im, siann = s1()
            for fig in sfig(siann):
                st.plotly_chart(fig, use_container_width=True)

        elif i == '3':
            im, un = u1()
            uh = u2(im, un)
            uth = u3(im, uh)
            ut = u5(im, un, uh)
            st.markdown(udf(un, uh, uth, ut).to_html(classes='dataframe'), unsafe_allow_html=True)
        elif i == '4':
            im, un = u1()
            for fig in ufig(un):
                st.plotly_chart(fig, use_container_width=True)
        elif i == '5':
            im, un = u1()
            uh = u2(im, un)
            uth = u3(im, uh)
            uths = u4(im, uth)
            ut = u5(im, un, uh)
            uhs = u6(im, un, uh, uth, ut)
            uts = u7(im, un, ut, uh)
            us = u8(im, un, uh, uts)
            st.markdown(usdf(us, uts, uths, uhs).to_html(classes='dataframe'), unsafe_allow_html=True)
        elif i == '6':
            st.write(tfig(), unsafe_allow_html=True)
        else:
            st.write('輸入錯誤')
        st.markdown('---')

# 添加生成的按鈕
if st.button("查詢"):
    if user_input:
        generator(user_input)
    else:
        st.warning("請先輸入")
        

# %% [markdown]
# <br><br><br>
# 輸出.py檔，然後在.py檔上把所有會呈現圖表、或者是以''''''括起來的部分刪除乾淨，否則會一直跳出來
# <br><br>

# %% [markdown]
# ### 
# - - - 
# #### *最後在終端機上 `F.py` 輸入 `streamlit run F.py` 就大功告成了！！*
# - - - 

# %% [markdown]
# 結果如repo中F.py所呈現
import pandas as pd
from difflib import SequenceMatcher

similar = lambda a, b : SequenceMatcher(None, a, b).ratio()
# print(similar('audet.org/', 'audi-mirando.blogspot.com/'))

df = pd.read_csv('phish_data.csv')

n = len(df)
for i in df.index:
    print(i)
    if df.iloc[i].URL != None:
        if df.iloc[i].URL.startswith("'") or df.iloc[i].URL[0].isdigit():
            df.iloc[i].URL = df.iloc[i].Label = None
        elif i < n-1 and similar(df.iloc[i].URL, df.iloc[i+1].URL) > 0.35:
            sameDomainList = []
            tempIndex = i
            while True:
                if tempIndex > n-2 or (similar(df.iloc[tempIndex].URL, df.iloc[tempIndex + 1].URL) < 0.35):
                    break
                sameDomainList.append(tempIndex + 1)
                tempIndex = tempIndex + 1
            # print(sameDomainList)
            for j in sameDomainList:
                df.iloc[j].URL = df.iloc[j].Label = None

df.to_csv('tempNaN2.csv')
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)
df.to_csv('newData2.csv')
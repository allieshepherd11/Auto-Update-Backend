import pandas as pd
import pandas as pd
import plotly.graph_objects as go
def plot(x,y,title='Drilling'):
    trace1 = go.Scatter(
        x=x,
        y=y,
        mode='lines',  
        marker=dict(
            size=10,
            color='green'
        ),
        name='Hole Depth',
        #text=ids
    )
    
    layout = go.Layout(
        title=title,
        xaxis=dict(title='Idx'),
        yaxis=dict(title='Depth [ft]')
    )   
    fig = go.Figure(data=[trace1], layout=layout)

    fig.show()

s = pd.read_excel("C:\\Users\\plaisancem\\Downloads\\Revenue Summary.xlsx",sheet_name=None)
dfs = []
for sheet_name, df in s.items():
    print(f"Sheet Name: {sheet_name}")
    dfs.append(df)

df = pd.concat(dfs)
print(df)
k = ['Property Description','Owner Net Value','Check Date']
d = [col for col in df.columns if col not in k]
df = df.drop(d,axis=1)
print(df)
wells = {}
for idx,row in df.iterrows(): 
    w = row['Property Description']
    d = row['Check Date']
    r = row['Owner Net Value']
    if w not in wells.keys():
        wells[w] = {'dates':[], 'net': []}
        wells[w]['dates'].append(d)
        wells[w]['net'].append(r)
    else:
        f = False
        for idx,i in enumerate(wells[w]['dates']):
            if i == d:
                wells[w]['net'][idx] += r
                f = True
        if not f:
            wells[w]['dates'].append(d)
            wells[w]['net'].append(r)

for well in wells.keys():
    plot(wells[well]['dates'],wells[well]['net'],well)
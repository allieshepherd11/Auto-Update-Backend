import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

df = pd.read_csv('data.csv')

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='South Texas Dashboard'),
    dcc.Dropdown(id='well_name', 
    options=[{'label': i, 'value': i} for i in df['Well Name'].unique()],
    value='Aaron #1'),
    dcc.Graph(id='production_graph')
])

@app.callback(
    Output(component_id = 'production_graph', component_property='figure'),
    Input(component_id = 'well_name', component_property='value')
)

def update_graph(well_name):
    filtered_well = df[df['Well Name'] == well_name]
    max_prod = filtered_well['Oil (BBLS)'].max()
    line_fig = px.line(filtered_well, x='Date', y='Oil (BBLS)', color_discrete_sequence=['green'], range_y=[0, max_prod], title=f'Oil Production for {well_name}')
    return line_fig

if __name__ == '__main__':
    app.run_server(debug=True)
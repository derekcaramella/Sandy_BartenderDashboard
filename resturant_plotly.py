# Import necessary modules
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from datetime import date

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
restaurant_name = 'Beach Side Bar'
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, update_title=restaurant_name + 'Management')

# https://www.tasteofhome.com/collection/easy-mixed-drinks/
order_df = pd.DataFrame({
    'order_id': ['00001', '00002', '00003', '00004', '00005', '00006', '00007', '00008', '00009'],
    'drink_name': ['Red Sangria', 'French 75', 'French 75', 'French 75', 'Chocolate Martini', 'Moscow Mule',
                   'Chocolate Martini',
                   'Spiked Lemonade', 'Bloody Mary'],
    'drink_price': [12, 11, 11, 13, 11, 10, 11, 8, 10],
    'order_date': ['1/1/2021', '1/1/2021', '1/1/2021', '1/1/2021', '1/15/2021', '1/31/2021', '2/1/2021', '2/15/2021',
                   '2/29/2021']
})

completed_orders_df = pd.DataFrame({
    'order_id': ['00001', '00002', '00003', '00004', '00005', '00006', '00007', '00008', '00009'],
    'bartender_name': ['Derek', 'Derek', 'Lisa', 'Tapan', 'Derek', 'Derek', 'Lisa', 'Tapan', 'Lisa']
})

join_df = pd.merge(order_df, completed_orders_df)
print(join_df)

range_slider_numdate = [x for x in range(len(order_df['order_date'].unique()))]

revenue_timeline_fig = px.bar(order_df, x='order_date', y='drink_price', color='drink_name', title='Revenue',
                              labels=dict(order_date="Order Date", drink_price='Revenue', drink_name='Drink Type'))
revenue_timeline_fig.update_xaxes(rangeslider_visible=False)
revenue_timeline_fig.update_layout(transition_duration=500)

order_pie_fig = px.pie(order_df, values='drink_price', names='drink_name', title='Drink Contribution to Revenue')

bartender_revenue_fig = px.area(join_df, x='order_date', y='drink_price', color='bartender_name')

app.layout = html.Div(children=[
    html.H1(children=restaurant_name),

    # transform every unique date to a number

    # then in the Slider
    html.Div(children=[
        dcc.RangeSlider(min=range_slider_numdate[0],  # the first date
                        max=range_slider_numdate[-1],  # the last date
                        value=[range_slider_numdate[0], range_slider_numdate[-1]],  # default: the first
                        marks={numd: date for numd, date in zip(range_slider_numdate, order_df['order_date'].unique())})
    ]),

    html.Div(children=
             dcc.Dropdown(id='drinks-dropdown',
                          options=[{'label': i['drink_name'], 'value': i['drink_name']} for i in
                                   order_df.drop_duplicates('drink_name').to_dict('records')],
                          multi=True,
                          placeholder='Filter by drink',
                          style={'padding': '5px 10px'})
             ),

    html.Div(children=
             dcc.Dropdown(id='bartender-dropdown',
                          options=[{'label': i['bartender_name'], 'value': i['bartender_name']} for i in
                                   completed_orders_df.drop_duplicates('bartender_name').to_dict('records')],
                          multi=True,
                          placeholder='Filter by bartender',
                          style={'padding': '5px 10px'})
             ),

    html.Div(children=[
        dcc.Graph(id='revenue-timeline-fig', figure=revenue_timeline_fig,
                  style={'width': '48%', 'display': 'inline-block', 'padding': '0px 10px'}),
        dcc.Graph(id='order-pie-fig', figure=order_pie_fig,
                  style={'width': '48%', 'display': 'inline-block', 'padding': '0px 10px'})
    ]),

    html.Div(children=[
        dcc.Graph(id='bartender-revenue-fig', figure=bartender_revenue_fig,
                  style={'width': '50%', 'display': 'inline-block', 'padding': '0px 10px'})
        # dcc.Graph(id='order-pie-fig', figure=order_pie_fig,
        #           style={'width': '32%', 'display': 'inline-block', 'padding': '0px 10px'})
    ])
])


@app.callback(
    [dash.dependencies.Input('demo-dropdown', 'value')])
def update_output(value):
    print(value)
    return value


if __name__ == '__main__':
    app.run_server(debug=True)

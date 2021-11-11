# Import necessary modules
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import ast
import datetime
from betaweb_ssh_tunnel import MySQLTunnel
import xlsxwriter
import io


host = 'betaweb.csug.rochester.edu'
port = 22
betaweb_username = 'dcaramel'
betaweb_password = 'PladisTurtles'
default_table = 'dcaramel_1'
local_host = '127.0.0.1'
local_port = 3306
connection = MySQLTunnel(host, port, betaweb_username, betaweb_password, default_table, local_host, local_port)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']  # External styler, can change but don't need to
restaurant_name = 'Sandy'  # restaurant name to be posted
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)  # set up the application
app.title = str(restaurant_name + ' Dashboard')  # Set Tab title

order_df = connection.query('SELECT * FROM Orders;')
completed_order_df = connection.query('SELECT * FROM CompletedOrders;')
completed_order_df['Year'] = pd.to_datetime(completed_order_df['Completed_time']).dt.strftime('%Y')
completed_order_df['Day'] = pd.to_datetime(completed_order_df['Completed_time']).dt.date
completed_order_df['Week'] = pd.to_datetime(completed_order_df['Completed_time']).dt.strftime('%YW%U')
completed_order_df['Month'] = pd.to_datetime(completed_order_df['Completed_time']).dt.strftime('%YM%m')
completed_order_df['Quarter'] = pd.to_datetime(completed_order_df['Completed_time']).dt.to_period('Q')
completed_order_df['Quarter'] = completed_order_df['Quarter'].dt.strftime('%YQ%q')

bartenders_df = connection.query('SELECT Bartender_id, CONCAT(Bartender_id, ". ", First_name, " ", Last_name) AS '
                                 'Bartender_full_name FROM Bartenders;').sort_values('Bartender_full_name')
orderable_items_df = connection.query('SELECT * FROM OrderableItems;').sort_values('Item_name')
supply_items_df = connection.query('SELECT * FROM ItemSupplies;').sort_values('Item_name')
employment_types_df = connection.query('SELECT * FROM EmploymentTypes;').sort_values('Employment_type_desc')

default_date_aggregate = 'Month'
join_order_df = pd.merge(order_df, completed_order_df)  # Join dfs so I can get bartender profit
join_order_df = pd.merge(join_order_df, bartenders_df, left_on='Bartender_service', right_on='Bartender_id')
join_order_df['Service_time'] = (join_order_df['Completed_time'] - join_order_df['Order_time']).dt.seconds

drink_revenue_df = pd.merge(join_order_df, orderable_items_df, left_on='Order_item', right_on='Item_id')
drink_revenue_df = drink_revenue_df.groupby(['Item_name', default_date_aggregate], as_index=False).sum()
drink_revenue_df = drink_revenue_df.sort_values([default_date_aggregate, 'Item_name'])

bartender_profit_df = pd.merge(join_order_df, orderable_items_df, left_on='Order_item', right_on='Item_id')
bartender_profit_df = bartender_profit_df.groupby([default_date_aggregate, 'Bartender_full_name'], as_index=False).sum()

# bartender_lag_df = pd.merge(join_order_df, bartenders_df, left_on='Bartender_service', right_on='Bartender_id')
bartender_lag_df = join_order_df.sort_values('Bartender_full_name')

# A range slider does not work with dates only numbers, so we create a list of the unique dates so we have numbers
unique_dates = completed_order_df[default_date_aggregate].unique()
unique_dates = sorted(unique_dates, key=lambda m: datetime.datetime.strptime(m, '%YM%m'))
unique_dates = [str(x) for x in unique_dates]
range_slider_number_date = [x for x in range(0, len(unique_dates))]
# A dictionary that displays the date to the number generated above
range_slider_dict = {number_date: date for number_date, date in zip(range_slider_number_date, unique_dates)}

"""
Dropdown Options List follow this format:
[{'label': 'New York City', 'value': 'NYC'},
{'label': 'Montreal', 'value': 'MTL'},
{'label': 'San Francisco', 'value': 'SF'}]
"""
# List comprehension for drink & bartender dropdown options. The label & value are the same & we drop duplicates
drinks_options_dict = [{'label': i['Item_name'], 'value': i['Item_id']} for
                       i in orderable_items_df.dropna().to_dict('records')]
bartender_options_dict = [{'label': i['Bartender_full_name'], 'value': i['Bartender_id']} for i in
                          bartenders_df.dropna().to_dict('records')]
item_supplies_options_dict = [{'label': i['Item_name'], 'value': i['Item_id']} for i in
                              supply_items_df.dropna().to_dict('records')]
employment_types_options_dict = [{'label': i['Employment_type_desc'], 'value': i['Employment_id']} for i in
                                 employment_types_df.dropna().to_dict('records')]

drinks_options_values = orderable_items_df['Item_id'].unique()
bartender_options_values = bartenders_df['Bartender_id'].unique()
item_supplies_options_values = supply_items_df['Item_id'].unique()
employment_types_options_values = employment_types_df['Employment_id'].unique()

drinks_options_values = sorted(drinks_options_values)
bartender_options_values = sorted(bartender_options_values)
item_supplies_options_values = sorted(item_supplies_options_values)
employment_types_options_values = sorted(employment_types_options_values)

# Timeline stacked bar graph of drink revenue based on the date, joined dataframe for callback by bartender
revenue_timeline_fig = px.bar(drink_revenue_df, x=default_date_aggregate, y='Item_price', color='Item_name',
                              title='Revenue',
                              labels=dict(order_date='Order Date', Item_name='Drink Type', Item_price='Revenue'))
revenue_timeline_fig.update_xaxes(rangeslider_visible=False)  # We have the code, but this places a slider
revenue_timeline_fig.update_layout(transition_duration=500)  # Responsiveness of the slider
#
# Pie graph of the contribution of the specific drink to the total revenue, joined dataframe for callback by bartender
order_pie_fig = px.pie(drink_revenue_df, values='Item_price', names='Item_name', title='Drink Contribution to Revenue')

# Stack line graph that shows the amount of revenue generated by each bartender, joined dataframe for callback by drink
bartender_revenue_fig = px.area(bartender_profit_df, x=default_date_aggregate, y='Item_price',
                                color='Bartender_full_name',
                                title='Bartender Completed Orders',
                                labels=dict(order_date='Order Date', Item_price='Revenue',
                                            Bartender_full_name='Bartender'))

bartender_order_completion_fig = px.histogram(bartender_lag_df, x='Service_time', color='Bartender_full_name',
                                              marginal='violin',
                                              title='Bartender Order Completion Time',
                                              histnorm='probability density',
                                              labels=dict(Bartender_full_name='Bartender',
                                                          Service_time='Time Lag (minutes)'))

# layout the application, each div has children
app.layout = html.Div(children=[
    html.Div(children=[
        html.H1(id='restaurant_name', children=restaurant_name, style={'display': 'inline'}),
        html.Button(id='download-dataframe-button', children='Download Data',
                    style={'float': 'right', 'vertical-align': 'bottom', 'bottom': '0', 'margin-top': '0px',
                           'backgroundColor': '#4CA9B9', 'color': '#E9D3AC'}),
        dcc.Download(id='download-dataframe-xlsx')
        ], style={'width': '100%'}),  # Display the restaurant names in H1 markdown

    html.Div(children=[
        dcc.ConfirmDialog(
            id='value-added-drinks-error-create-drink',
            message='Please, enter the correct value added drinks format. There should be only integers & a '
                    'comma to separate drink amounts per value added drink. Additionally, ensure you have the same '
                    'number of quantities (mL) and number of prices per bottle ($) to match the number of value '
                    'added drinks.'),
        dcc.ConfirmDialog(
            id='number-type-error-create-drink',
            message='Please, ensure you entered numeric information.'),
        dcc.ConfirmDialog(
            id='existing-drink-create-drink',
            message='This drink already exists, please, update the drink below.'),
        dcc.ConfirmDialog(
            id='existing-drink-create-value-added-drink',
            message='This drink already exists, please, update the drink below.'),
        dcc.ConfirmDialog(
            id='number-type-error-create-value-added-drink',
            message='Please, ensure you entered numeric information.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-create-drink',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-create-bartender',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-create-value-added-drink',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='value-added-drinks-error-update-drink',
            message='Please, enter the correct value added drinks format. There should be only integers & a '
                    'comma to separate drink amounts per value added drink. Additionally, ensure you have the same '
                    'number of quantities (mL) and number of prices per bottle ($) to match the number of value '
                    'added drinks.'),
        dcc.ConfirmDialog(
            id='number-type-error-update-drink',
            message='Please, ensure you entered numeric information.'),
        dcc.ConfirmDialog(
            id='number-type-error-update-value-added-drink',
            message='Please, ensure you entered numeric information.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-update-drink',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='existing-drink-update-drink',
            message='This drink already exists, please, update the drink, not rename the current drink.'),
        dcc.ConfirmDialog(
            id='existing-drink-update-value-added-drink',
            message='This drink already exists, please, update the drink, not rename the current drink.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-update-bartender',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-update-value-added-drink',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-delete-drink',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-delete-bartender',
            message='Please, complete user form.'),
        dcc.ConfirmDialog(
            id='complete-all-information-error-delete-value-added-drink',
            message='Please, complete user form.'),
    ]),

    # Date Range slider
    html.Div(children=[
        dcc.RangeSlider(id='date-range-slider',  # id for callback
                        min=range_slider_number_date[0],  # the first date
                        max=range_slider_number_date[-1],  # the last date
                        value=[range_slider_number_date[0], range_slider_number_date[-1]],  # From first to last
                        marks=range_slider_dict),
    ]),
    # Drinks dropdown menu for callback
    html.Div(children=
             dcc.Dropdown(id='drinks-dropdown',  # id for callback
                          options=drinks_options_dict,  # List dictionary for options
                          multi=True,  # Enable multiple selection
                          # value=drinks_options_values,  # All the unique instances in the df for first load
                          placeholder='Filter by drink',  # Prompt
                          style={'padding': '5px 10px'})  # Layout padding for good spacing
             ),

    # Bartender dropdown menu for callback
    html.Div(children=
             dcc.Dropdown(id='bartender-dropdown',  # id for callback
                          options=bartender_options_dict,
                          multi=True,  # Enable multiple selection
                          # All the unique instances in the df for first load
                          # value=bartender_options_values,
                          placeholder='Filter by bartender',  # Prompt
                          style={'padding': '5px 10px'})  # Layout padding for good spacing
             ),

    # Date Aggregator menu for callback
    html.Div(children=
             dcc.Dropdown(id='date-aggregate-dropdown',  # id for callback
                          options=[
                              {'label': 'Day', 'value': 'Day'},
                              {'label': 'Week', 'value': 'Week'},
                              {'label': 'Month', 'value': 'Month'},
                              {'label': 'Quarter', 'value': 'Quarter'}],
                          value=default_date_aggregate,
                          multi=False,  # Disable multiple selection
                          placeholder='Aggregate Time Series',  # Prompt
                          style={'padding': '5px 10px'})  # Layout padding for good spacing
             ),

    # The revenue generated by drink time-series & revenue contribution pie graph div. These will be on the same line
    html.Div(children=[
        dcc.Graph(id='revenue-timeline-fig',  # id for callback
                  figure=revenue_timeline_fig,  # See figure above
                  style={'width': '48%', 'display': 'inline-block', 'padding': '0px 10px'}),  # Layout styling
        dcc.Graph(id='order-pie-fig',  # id for callback
                  figure=order_pie_fig,  # See figure above
                  style={'width': '48%', 'display': 'inline-block', 'padding': '0px 10px'})  # Layout styling
    ]),

    # Stacked line graph of bartender revenue
    html.Div(children=[
        dcc.Graph(id='bartender-revenue-fig',  # id for callback
                  figure=bartender_revenue_fig,  # See figure above
                  style={'width': '48%', 'display': 'inline-block', 'padding': '0px 10px'}),  # Layout styling
        dcc.Graph(id='bartender-order-completion-fig', figure=bartender_order_completion_fig,
                  style={'width': '48%', 'display': 'inline-block', 'padding': '0px 10px'})
    ]),

    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.H4(id='create-drink-userform-title', children='Create Drink'),  # Create Drink User Form Title
                dcc.Input(id='create-drink-userform-drink-name', placeholder='Drink Name', value='',
                          style={'width': '75%'}),
                html.Br(),
                dcc.Dropdown(id='create-drink-userform-value-added-drinks',  # id for callback
                             options=item_supplies_options_dict,
                             value=[],
                             multi=True,  # Enable multiple selection
                             placeholder='Value Added Drinks'),  # Prompt
                dcc.Input(id='create-drink-userform-value-added-quantities',
                          placeholder=u'Drink\u2081 Amount,Drink\u2082 Amount,...,Drink\u2099 Amount',
                          value='', style={'width': '85%'}),
                html.Br(),
                dcc.Input(id='create-drink-userform-price',
                          placeholder='Drink Price ($)',
                          value='', style={'width': '75%'}),
                html.Br(),
                html.Button(children='Create Drink', id='create-drink-userform-submit-entry')],
                style={'width': '30%', 'padding': '0px 10px', 'vertical-align': 'top', 'display': 'inline-block'}),
            # Layout styling

            html.Div(children=[
                html.H4(id='create-bartender-userform-title', children='Create Bartender'),
                # Create Drink User Form Title
                dcc.Input(id='create-bartender-userform-bartender-first-name', placeholder='Bartender First Name',
                          value='', style={'width': '75%'}),
                html.Br(),
                dcc.Input(id='create-bartender-userform-bartender-last-name', placeholder='Bartender Last Name',
                          value='', style={'width': '75%'}),
                dcc.Dropdown(id='create-bartender-userform-employment-type',  # id for callback
                             options=employment_types_options_dict,
                             value='',
                             multi=False,  # Disable multiple selection
                             placeholder='Employment Type'),  # Prompt
                html.Button(children='Create Bartender', id='create-bartender-userform-submit-entry')],
                style={'width': '30%', 'padding': '0px 10px', 'vertical-align': 'top', 'display': 'inline-block'}),

            html.Div(children=[
                html.H4(id='create-value-added-drink-userform-title', children='Create Value Added Drink'),
                dcc.Input(id='create-value-added-drink-userform-drink-name', placeholder='Value Added Drink Name',
                          value='', style={'width': '75%'}),
                html.Br(),
                dcc.Input(id='create-value-added-drink-userform-drink-bottle-size',
                          placeholder='Value Added Bottle Size (mL)', value='', style={'width': '75%'}),
                html.Br(),
                dcc.Input(id='create-value-added-drink-userform-drink-bottle-price',
                          placeholder='Value Added Price ($)', value='', style={'width': '75%'}),
                html.Button(children='Create Value Added Drink', id='create-value-added-drink-userform-submit-entry')],
                style={'width': '30%', 'padding': '0px 5px', 'vertical-align': 'top', 'display': 'inline-block'})
        ]),

        html.Div(children=[
                    html.Div(children=[
                        html.H4(id='update-drink-userform-title', children='Update Drink'),  # Update Drink Form Title
                        dcc.Dropdown(id='update-drink-userform-drink-id',  # id for callback
                                     options=drinks_options_dict,
                                     value='',
                                     multi=False,  # Enable multiple selection
                                     placeholder='Existing Drink Name',
                                     style={'width': '75%'}),
                        dcc.Input(id='update-drink-userform-drink-name',
                                  placeholder='New Drink Name',
                                  value='', style={'width': '85%'}),
                        dcc.Dropdown(id='update-drink-userform-value-added-drinks',  # id for callback
                                     options=item_supplies_options_dict,
                                     value=[],
                                     multi=True,  # Enable multiple selection
                                     placeholder='New Value Added Drinks'),  # Prompt
                        dcc.Input(id='update-drink-userform-value-added-quantities',
                                  placeholder=u'New Drink\u2081 Amount,New Drink\u2082 Amount,...,New Drink\u2099 Amount',
                                  value='', style={'width': '85%'}),
                        html.Br(),
                        dcc.Input(id='update-drink-userform-price',
                                  placeholder='New Drink Price ($)',
                                  value='', style={'width': '75%'}),
                        html.Button(children='Update Drink', id='update-drink-userform-submit-entry')],
                        style={'width': '30%', 'padding': '0px 10px', 'vertical-align': 'top', 'display': 'inline-block'}),
                    # Layout styling

                    html.Div(children=[
                        html.H4(id='update-bartender-userform-title', children='Update Bartender'),
                        dcc.Dropdown(id='update-bartender-userform-bartender-id',  # id for callback
                                     options=bartender_options_dict,
                                     value='',
                                     multi=False,  # Enable multiple selection
                                     placeholder='Existing Bartender',
                                     style={'width': '75%'}),
                        dcc.Input(id='update-bartender-userform-bartender-first-name',
                                  placeholder='New Bartender First Name',
                                  value='', style={'width': '75%'}),
                        html.Br(),
                        dcc.Input(id='update-bartender-userform-bartender-last-name',
                                  placeholder='New Bartender Last Name',
                                  value='', style={'width': '75%'}),
                        html.Br(),
                        dcc.Dropdown(id='update-bartender-userform-employment-type',  # id for callback
                                     options=employment_types_options_dict,
                                     value='',
                                     multi=False,  # Disable multiple selection
                                     placeholder='New Employment Type'),  # Prompt
                        html.Button(children='Update Bartender', id='update-bartender-userform-submit-entry')],
                        style={'width': '30%', 'padding': '0px 10px', 'vertical-align': 'top', 'display': 'inline-block'}),

                    html.Div(children=[
                        html.H4(id='update-value-added-drink-userform-title', children='Update Value Added Drink'),
                        dcc.Dropdown(id='update-value-added-drink-userform-drink-id',  # id for callback
                                     options=item_supplies_options_dict,
                                     value='',
                                     multi=False,  # Enable multiple selection
                                     placeholder='New Value Added Drink Name',
                                     style={'width': '75%'}),
                        dcc.Input(id='update-value-added-drink-userform-drink-name',
                                  placeholder='New Value Added Drink Name', value='', style={'width': '75%'}),
                        dcc.Input(id='update-value-added-drink-userform-drink-bottle-size',
                                  placeholder='New Value Added Bottle Size (mL)', value='', style={'width': '75%'}),
                        html.Br(),
                        dcc.Input(id='update-value-added-drink-userform-drink-bottle-price',
                                  placeholder='New Value Added Price ($)', value='', style={'width': '75%'}),
                        html.Button(children='Update Value Added Drink', id='update-value-added-drink-userform-submit-entry')],
                        style={'width': '30%', 'padding': '0px 5px', 'vertical-align': 'top', 'display': 'inline-block'})
                ]),

        html.Div(children=[
            html.Div(children=[
                html.H4(id='delete-drink-userform-title', children='Delete Drink'),
                dcc.Dropdown(id='delete-drink-userform-drink-name',  # id for callback
                             options=drinks_options_dict,
                             multi=False,  # Enable multiple selection
                             # All the unique instances in the df for first load
                             value='',
                             placeholder='Drink Name'),  # Prompt
                html.Button(children='Delete Drink', id='delete-drink-userform-submit-entry')],
                style={'width': '30%', 'padding': '0px 5px', 'vertical-align': 'top', 'display': 'inline-block'}),

            html.Div(children=[
                html.H4(id='delete-bartender-userform-title', children='Delete Bartender'),
                dcc.Dropdown(id='delete-bartender-userform-bartender-name',  # id for callback
                             options=bartender_options_dict,
                             multi=False,  # Enable multiple selection
                             # All the unique instances in the df for first load
                             value='',
                             placeholder='Bartender Full Name'),  # Prompt
                html.Button(children='Delete Bartender', id='delete-bartender-userform-submit-entry')],
                style={'width': '30%', 'padding': '0px 5px', 'vertical-align': 'top', 'display': 'inline-block'}),

            html.Div(children=[
                html.H4(id='delete-value-added-drink-userform-title', children='Delete Value Added Drink'),
                dcc.Dropdown(id='delete-value-added-drink-userform-name',  # id for callback
                             options=item_supplies_options_dict,
                             multi=False,  # Enable multiple selection
                             # All the unique instances in the df for first load
                             value='',
                             placeholder='Value Added Drink Name'),  # Prompt
                html.Button(children='Delete Value Added Drink', id='delete-value-added-drink-userform-submit-entry')],
                style={'width': '30%', 'padding': '0px 5px', 'vertical-align': 'top', 'display': 'inline-block'})
        ])

        # Layout styling
    ], style={'width': '100%', 'display': 'inline-block'})

])

create_drinks_n_of_clicks = 0
create_bartender_n_of_clicks = 0
create_value_added_n_of_clicks = 0
update_drinks_n_of_clicks = 0
update_bartender_n_of_clicks = 0
update_value_added_n_of_clicks = 0
delete_drink_n_of_clicks = 0
delete_bartender_n_of_clicks = 0
delete_value_added_n_of_clicks = 0


@app.callback(
    Output('drinks-dropdown', 'options'),
    Output('bartender-dropdown', 'options'),
    Output('create-drink-userform-value-added-drinks', 'options'),
    Output('update-drink-userform-drink-id', 'options'),
    Output('update-drink-userform-value-added-drinks', 'options'),
    Output('update-bartender-userform-bartender-id', 'options'),
    Output('update-value-added-drink-userform-drink-id', 'options'),
    Output('delete-drink-userform-drink-name', 'options'),
    Output('delete-bartender-userform-bartender-name', 'options'),
    Output('delete-value-added-drink-userform-name', 'options'),
    [Input('date-range-slider', 'value')]
)
def update_base_queries(_):
    global order_df, completed_order_df, bartenders_df, orderable_items_df, supply_items_df, employment_types_df, \
        join_order_df, drinks_options_dict, bartender_options_dict, item_supplies_options_dict, \
        employment_types_options_dict, drinks_options_values, bartender_options_values, item_supplies_options_values

    try:
        order_df = connection.query('SELECT * FROM Orders;')
        completed_order_df = connection.query('SELECT * FROM CompletedOrders;')
        completed_order_df['Year'] = pd.to_datetime(completed_order_df['Completed_time']).dt.strftime('%Y')
        completed_order_df['Day'] = pd.to_datetime(completed_order_df['Completed_time']).dt.date
        completed_order_df['Week'] = pd.to_datetime(completed_order_df['Completed_time']).dt.strftime('%YW%U')
        completed_order_df['Month'] = pd.to_datetime(completed_order_df['Completed_time']).dt.strftime('%YM%m')
        completed_order_df['Quarter'] = pd.to_datetime(completed_order_df['Completed_time']).dt.to_period('Q')
        completed_order_df['Quarter'] = completed_order_df['Quarter'].dt.strftime('%YQ%q')

        bartenders_df = connection.query('SELECT Bartender_id, CONCAT(Bartender_id, ". ", First_name, " ", Last_name) AS '
                                         'Bartender_full_name FROM Bartenders;').sort_values('Bartender_full_name')
        orderable_items_df = connection.query('SELECT * FROM OrderableItems;').sort_values('Item_name')
        supply_items_df = connection.query('SELECT * FROM ItemSupplies;').sort_values('Item_name')
    except:
        raise PreventUpdate

    join_order_df = pd.merge(order_df, completed_order_df)  # Join dfs so I can get bartender profit
    join_order_df = pd.merge(join_order_df, bartenders_df, left_on='Bartender_service', right_on='Bartender_id')
    join_order_df['Service_time'] = (join_order_df['Completed_time'] - join_order_df['Order_time']).dt.seconds

    # List comprehension for drink & bartender dropdown options. The label & value are the same & we drop duplicates
    drinks_options_dict = [{'label': i['Item_name'], 'value': i['Item_id']} for
                           i in orderable_items_df.dropna().to_dict('records')]
    bartender_options_dict = [{'label': i['Bartender_full_name'], 'value': i['Bartender_id']} for i in
                              bartenders_df.dropna().to_dict('records')]
    item_supplies_options_dict = [{'label': i['Item_name'], 'value': i['Item_id']} for i in
                                  supply_items_df.dropna().to_dict('records')]

    drinks_options_values = orderable_items_df['Item_id'].unique()
    bartender_options_values = bartenders_df['Bartender_id'].unique()
    item_supplies_options_values = supply_items_df['Item_id'].unique()

    drinks_options_values = sorted(drinks_options_values)
    bartender_options_values = sorted(bartender_options_values)
    item_supplies_options_values = sorted(item_supplies_options_values)

    return drinks_options_dict, bartender_options_dict, item_supplies_options_dict, drinks_options_dict, \
           item_supplies_options_dict, bartender_options_dict, item_supplies_options_dict, drinks_options_dict, \
           bartender_options_dict, item_supplies_options_dict


@app.callback(
    Output('download-dataframe-xlsx', 'data'),
    Input('download-dataframe-button', 'n_clicks'),
    prevent_initial_call=True
)
def download_data(n_clicks):
    export = io.BytesIO()
    writer = pd.ExcelWriter(export, engine='xlsxwriter')

    bartenders = connection.query('SELECT * FROM Bartenders;')
    completed_orders = connection.query('SELECT * FROM CompletedOrders;')
    employment_types = connection.query('SELECT * FROM EmploymentTypes;')
    item_supplies = connection.query('SELECT * FROM ItemSupplies;')
    orderable_items = connection.query('SELECT * FROM OrderableItems;').sort_values('Item_name')
    orders = connection.query('SELECT * FROM Orders;')
    recipes = connection.query('SELECT * FROM Recipes;')

    bartenders.to_excel(writer, sheet_name='Bartenders', index=False)
    completed_orders.to_excel(writer, sheet_name='Completed Orders', index=False)
    employment_types.to_excel(writer, sheet_name='Employment Types', index=False)
    item_supplies.to_excel(writer, sheet_name='Item Supplies', index=False)
    orderable_items.to_excel(writer, sheet_name='Orderable Items', index=False)
    orders.to_excel(writer, sheet_name='Orders', index=False)
    recipes.to_excel(writer, sheet_name='Recipes', index=False)
    writer.save()
    export_data = export.getvalue()

    return dcc.send_bytes(export_data, 'DataFrame.xlsx')


# Callbacks are order sensitive, the order matters when inputting parameters into the output function
@app.callback(
    Output('revenue-timeline-fig', 'figure'),  # First return from function is the revenue timeline
    Output('order-pie-fig', 'figure'),  # Second return from function is the order pie figure
    Output('bartender-revenue-fig', 'figure'),  # Third return from function is the bartender revenue figure
    Output('bartender-order-completion-fig', 'figure'),
    # We convert these inputs to lists because they are multi input options, if was a single it doesn't need to be list
    [Input('date-range-slider', 'value')],  # First parameter into function is the date range slider
    [Input('drinks-dropdown', 'value')],  # Second parameter into function is the drinks dropdown
    [Input('bartender-dropdown', 'value')],  # Third parameter into function is the bartender dropdown
    Input('date-aggregate-dropdown', 'value')
)
def update_figures(range_slider, drinks_dropdown, bartender_dropdown, date_aggregate_dropdown):
    if date_aggregate_dropdown is None or date_aggregate_dropdown == '':
        date_aggregate_dropdown = default_date_aggregate
    if drinks_dropdown is None or drinks_dropdown == []:
        drinks_dropdown = drinks_options_values
    if bartender_dropdown is None or bartender_dropdown == []:
        bartender_dropdown = bartender_options_values
    date_ranges = unique_dates[range_slider[0]:range_slider[1] + 1]

    # Filter date in between the range slider. The range slider will return the integers corresponding to the date

    callback_join_order_df = join_order_df[join_order_df['Order_item'].isin(drinks_dropdown)]  # Filter by drink names
    callback_join_order_df = callback_join_order_df[
        callback_join_order_df['Bartender_id'].isin(bartender_dropdown)]  # Filter by bartender names
    callback_join_order_df = callback_join_order_df[
        callback_join_order_df[default_date_aggregate].isin(date_ranges)]  # Filter by bartender names

    callback_drink_revenue_df = pd.merge(callback_join_order_df, orderable_items_df, left_on='Order_item',
                                         right_on='Item_id')

    callback_drink_revenue_df = callback_drink_revenue_df.groupby(['Item_name', date_aggregate_dropdown],
                                                                  as_index=False).sum()

    callback_bartender_profit_df = pd.merge(callback_join_order_df, orderable_items_df, left_on='Order_item',
                                            right_on='Item_id')
    callback_bartender_profit_df = callback_bartender_profit_df.groupby(
        [date_aggregate_dropdown, 'Bartender_full_name'], as_index=False).sum()

    callback_bartender_lag_df = callback_join_order_df.sort_values('Bartender_full_name')

    callback_revenue_timeline_fig = px.bar(callback_drink_revenue_df, x=date_aggregate_dropdown, y='Item_price',
                                           color='Item_name',
                                           title='Revenue',
                                           labels=dict(order_date='Order Date', Item_name='Drink Type',
                                                       Item_price='Revenue'))
    callback_revenue_timeline_fig.update_xaxes(rangeslider_visible=False)  # We have the code, but this places a slider
    callback_revenue_timeline_fig.update_layout(transition_duration=500)  # Responsiveness of the slider

    # Pie graph of the contribution of the specific drink to the total revenue, joined dataframe for callback by
    # bartender
    callback_order_pie_fig = px.pie(callback_drink_revenue_df, values='Item_price', names='Item_name',
                                    title='Drink Contribution to Revenue')

    # Stack line graph that shows the amount of revenue generated by each bartender, joined dataframe for callback by
    # drink
    callback_bartender_revenue_fig = px.area(callback_bartender_profit_df, x=date_aggregate_dropdown, y='Item_price',
                                             color='Bartender_full_name',
                                             title='Bartender Completed Orders',
                                             labels=dict(order_date='Order Date', Item_price='Revenue',
                                                         Bartender_full_name='Bartender'))

    callback_bartender_order_completion_fig = px.histogram(callback_bartender_lag_df, x='Service_time',
                                                           color='Bartender_full_name',
                                                           marginal='violin',
                                                           title='Bartender Order Completion Time',
                                                           histnorm='probability density',
                                                           labels=dict(Bartender_full_name='Bartender',
                                                                       Service_time='Time Lag (minutes)'))
    # Return function must be in order of the Outputs in the callback decorator, these will render in the
    # corresponding Divs
    return callback_revenue_timeline_fig, callback_order_pie_fig, callback_bartender_revenue_fig, \
           callback_bartender_order_completion_fig


# Create forms
@app.callback(
    Output('value-added-drinks-error-create-drink', 'displayed'),
    Output('number-type-error-create-drink', 'displayed'),
    Output('complete-all-information-error-create-drink', 'displayed'),
    Output('existing-drink-create-drink', 'displayed'),
    Output('create-drink-userform-drink-name', 'value'),
    Output('create-drink-userform-value-added-drinks', 'value'),
    Output('create-drink-userform-value-added-quantities', 'value'),
    Output('create-drink-userform-price', 'value'),
    Input('create-drink-userform-drink-name', 'value'),
    [Input('create-drink-userform-value-added-drinks', 'value')],
    Input('create-drink-userform-value-added-quantities', 'value'),
    Input('create-drink-userform-price', 'value'),
    Input('create-drink-userform-submit-entry', 'n_clicks')

)
def create_drink_user_form(drink_name, value_added_drinks, value_added_drinks_quantities, drink_price,
                           create_drink_clicks):
    global create_drinks_n_of_clicks

    # If create drinks is not None & the the local create value added clicks is greater than the global
    # value added number of drinks
    if create_drink_clicks is not None and create_drink_clicks > create_drinks_n_of_clicks:
        # If the parameters are empty, we can do this because the default values are defined.
        if drink_name == '' or value_added_drinks == [] or value_added_drinks_quantities == '':
            create_drinks_n_of_clicks += 1  # Increase global clicks by one
            # Return fill the damn template error with no updates
            return False, False, True, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        # If the template is completed for each quantity in the value added drink quantities, check if the quantities
        # are raw numbers
        for quantity in value_added_drinks_quantities.split(','):
            try:
                float(quantity)
            except ValueError:
                create_drinks_n_of_clicks += 1  # Increase global clicks by one
                # Trigger input only numbers error with no updates
                return False, True, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        # Make the value added drink quantities into a tuple
        value_added_drinks_quantities = ast.literal_eval('(' + value_added_drinks_quantities + ')')
        if isinstance(value_added_drinks_quantities, int) or isinstance(value_added_drinks_quantities, float) or isinstance(value_added_drinks_quantities, str):
            value_added_drinks_quantities = [value_added_drinks_quantities]

        # Check to make sure the length of value added drinks equals drink amounts
        if len(value_added_drinks_quantities) != len(value_added_drinks):
            create_drinks_n_of_clicks += 1  # Increase global clicks by one
            # Prompt the user to correct the lengths of the recipe
            return True, False, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Ensure we can float the drink price
        try:
            drink_price = float(drink_price)
        except ValueError:
            create_drinks_n_of_clicks += 1  # Increase the global clicks by one
            # Trigger the numeric error
            return False, True, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Test if drink already exists
        existing_drink_names = connection.query('SELECT Item_name FROM OrderableItems;')['Item_name'].values.tolist()
        if drink_name in existing_drink_names:
            create_drinks_n_of_clicks += 1  # Increase the global clicks by one
            return False, False, False, True, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Database Inserts
        drink_id = int(connection.query('SELECT MAX(Item_id) FROM OrderableItems;').values[0]) + 1
        insert_tuple = (drink_id, drink_name, drink_price, 1)
        connection.non_query_statements('INSERT INTO OrderableItems VALUES ' + str(insert_tuple) + ';')

        prefix_recipe_list = [drink_id] * len(value_added_drinks)  # Create list of the drink id n times to match recipe
        recipe = tuple(zip(prefix_recipe_list, value_added_drinks, value_added_drinks_quantities))  # Zip the lists
        if len(recipe) == 1:
            insert_tuple = str(recipe)[1:-2]
        else:
            insert_tuple = str(recipe)[1:-1]
        connection.non_query_statements('INSERT INTO Recipes VALUES ' + insert_tuple + ';')

        create_drinks_n_of_clicks += 1  # Increase the global clicks by one

        return False, False, False, False, '', [], '', ''  # Reset user form
    else:
        raise PreventUpdate


@app.callback(
    Output('complete-all-information-error-create-bartender', 'displayed'),
    Output('create-bartender-userform-bartender-first-name', 'value'),
    Output('create-bartender-userform-bartender-last-name', 'value'),
    Output('create-bartender-userform-employment-type', 'value'),
    Input('create-bartender-userform-bartender-first-name', 'value'),
    Input('create-bartender-userform-bartender-last-name', 'value'),
    Input('create-bartender-userform-employment-type', 'value'),
    Input('create-bartender-userform-submit-entry', 'n_clicks')

)
def create_bartender_user_form(bartender_first_name, bartender_last_name, bartender_employment_type,
                               create_bartender_clicks):
    global create_bartender_n_of_clicks

    # If create bartender clicks is not None & the the local bartender clicks is greater than the global
    # value added number of drinks
    if create_bartender_clicks is not None and create_bartender_clicks > create_bartender_n_of_clicks:
        # Check to make sure it is not an empty form, we can do this by setting default value
        if bartender_first_name == '' or bartender_last_name == '' or bartender_employment_type == '':
            create_bartender_n_of_clicks += 1  # Increase global clicks
            # Trigger complete the form error with no updates
            return True, dash.no_update, dash.no_update, dash.no_update

        # Database insert
        bartender_id = int(connection.query('SELECT MAX(Bartender_id) FROM Bartenders;').values[0]) + 1
        insert_tuple = (bartender_id, bartender_first_name, bartender_last_name, bartender_employment_type)
        connection.non_query_statements('INSERT INTO Bartenders VALUES ' + str(insert_tuple) + ';')

        create_bartender_n_of_clicks += 1  # Increase global counter by one
        return False, '', '', ''  # Clear user form
    else:
        raise PreventUpdate  # No update


@app.callback(
    Output('complete-all-information-error-create-value-added-drink', 'displayed'),
    Output('number-type-error-create-value-added-drink', 'displayed'),
    Output('existing-drink-create-value-added-drink', 'displayed'),
    Output('create-value-added-drink-userform-drink-name', 'value'),
    Output('create-value-added-drink-userform-drink-bottle-size', 'value'),
    Output('create-value-added-drink-userform-drink-bottle-price', 'value'),
    Input('create-value-added-drink-userform-drink-name', 'value'),
    Input('create-value-added-drink-userform-drink-bottle-size', 'value'),
    Input('create-value-added-drink-userform-drink-bottle-price', 'value'),
    Input('create-value-added-drink-userform-submit-entry', 'n_clicks')
)
def create_value_added_drink_user_form(value_added_drink_name, value_added_bottle_size, value_added_bottle_price,
                                       create_value_added_clicks):
    global create_value_added_n_of_clicks

    # If create value added drinks is not None & the the local create value added clicks is greater than the global
    # value added number of drinks
    if create_value_added_clicks is not None and create_value_added_clicks > create_value_added_n_of_clicks:
        # If the inputs are empty throw error, we can do this with default errors
        if value_added_drink_name == '' or value_added_bottle_size == '' or value_added_bottle_price == '':
            create_value_added_n_of_clicks += 1  # Increase the global counter by one
            # Throw the complete the damn form error
            return True, False, False, dash.no_update, dash.no_update, dash.no_update

        # Attempt to float both bottle size & price to see if numbers
        try:
            value_added_bottle_size = float(value_added_bottle_size)
            value_added_bottle_price = float(value_added_bottle_price)
        except ValueError:
            create_value_added_n_of_clicks += 1  # Increase the global count by one
            # On error return the numeric error
            return True, False, False, dash.no_update, dash.no_update, dash.no_update

        existing_drink_names = connection.query('SELECT Item_name FROM ItemSupplies;')['Item_name'].values.tolist()
        if value_added_drink_name in existing_drink_names:
            create_value_added_n_of_clicks += 1  # Increase the global clicks by one
            return False, False, True, dash.no_update, dash.no_update, dash.no_update

        # Database inserts
        supply_item_id = int(connection.query('SELECT MAX(Item_id) FROM ItemSupplies;').values[0]) + 1
        insert_tuple = (supply_item_id, value_added_drink_name, value_added_bottle_size, value_added_bottle_price)
        connection.non_query_statements('INSERT INTO ItemSupplies VALUES ' + str(insert_tuple) + ';')
        create_value_added_n_of_clicks += 1  # Increase global counter by one
        return False, False, False, '', '', ''  # Clear Form
    else:
        raise PreventUpdate


# Update forms
@app.callback(
    Output('value-added-drinks-error-update-drink', 'displayed'),
    Output('number-type-error-update-drink', 'displayed'),
    Output('complete-all-information-error-update-drink', 'displayed'),
    Output('existing-drink-update-drink', 'displayed'),
    Output('update-drink-userform-drink-id', 'value'),
    Output('update-drink-userform-drink-name', 'value'),
    Output('update-drink-userform-value-added-drinks', 'value'),
    Output('update-drink-userform-value-added-quantities', 'value'),
    Output('update-drink-userform-price', 'value'),
    Input('update-drink-userform-drink-id', 'value'),
    Input('update-drink-userform-drink-name', 'value'),
    [Input('update-drink-userform-value-added-drinks', 'value')],
    Input('update-drink-userform-value-added-quantities', 'value'),
    Input('update-drink-userform-price', 'value'),
    Input('update-drink-userform-submit-entry', 'n_clicks')

)
def update_drink_user_form(drink_id, new_drink_name, value_added_drinks, value_added_drinks_quantities, drink_price,
                           update_drink_clicks):
    global update_drinks_n_of_clicks

    # If create drinks is not None & the the local create value added clicks is greater than the global
    # value added number of drinks
    if update_drink_clicks is not None and update_drink_clicks > update_drinks_n_of_clicks:
        # If the parameters are empty, we can do this because the default values are defined.
        if drink_id == '' or new_drink_name == '' or value_added_drinks == [] or value_added_drinks_quantities == '':
            update_drinks_n_of_clicks += 1  # Increase global clicks by one
            # Return fill the damn template error with no updates
            return False, False, True, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        # If the template is completed for each quantity in the value added drink quantities, check if the quantities
        # are raw numbers
        for quantity in value_added_drinks_quantities.split(','):
            try:
                float(quantity)
            except ValueError:
                update_drinks_n_of_clicks += 1  # Increase global clicks by one
                # Trigger input only numbers error with no updates
                return False, True, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        # Make the value added drink quantities into a tuple
        value_added_drinks_quantities = ast.literal_eval('(' + value_added_drinks_quantities + ')')
        if isinstance(value_added_drinks_quantities, int) or isinstance(value_added_drinks_quantities, float) or isinstance(value_added_drinks_quantities, str):
            value_added_drinks_quantities = [value_added_drinks_quantities]

        # Check to make sure the length of value added drinks equals drink amounts
        if len(value_added_drinks_quantities) != len(value_added_drinks):
            update_drinks_n_of_clicks += 1  # Increase global clicks by one
            # Prompt the user to correct the lengths of the recipe
            return True, False, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Ensure we can float the drink price
        try:
            drink_price = float(drink_price)
        except ValueError:
            update_drinks_n_of_clicks += 1  # Increase the global clicks by one
            # Trigger the numeric error
            return False, True, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Test if drink already exists
        existing_drink_names = connection.query('SELECT Item_name FROM OrderableItems;')['Item_name'].values.tolist()
        if new_drink_name in existing_drink_names:
            update_drinks_n_of_clicks += 1  # Increase the global clicks by one
            return False, False, False, True, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Database Update
        insert_tuple = (new_drink_name, drink_price, 1)
        sql_update = r'UPDATE OrderableItems SET Item_name="' + str(insert_tuple[0]) + r'", Item_price=' + str(insert_tuple[1]) + ', Available=' + str(insert_tuple[2]) + ' WHERE Item_id=' + str(drink_id) + ';'
        connection.non_query_statements(sql_update)

        prefix_recipe_list = [drink_id] * len(value_added_drinks)  # Create list of the drink id n times to match recipe
        recipe = tuple(zip(prefix_recipe_list, value_added_drinks, value_added_drinks_quantities))  # Zip the lists
        if len(recipe) == 1:
            insert_tuple = str(recipe)[1:-2]
        else:
            insert_tuple = str(recipe)[1:-1]
        connection.non_query_statements('DELETE FROM Recipes WHERE Finished_item_id=' + str(drink_id))
        connection.non_query_statements('INSERT INTO Recipes VALUES ' + insert_tuple + ';')

        update_drinks_n_of_clicks += 1  # Increase the global clicks by one

        return False, False, False, False, '', '', [], '', ''  # Reset user form
    else:
        raise PreventUpdate


@app.callback(
    Output('complete-all-information-error-update-bartender', 'displayed'),
    Output('update-bartender-userform-bartender-id', 'value'),
    Output('update-bartender-userform-bartender-first-name', 'value'),
    Output('update-bartender-userform-bartender-last-name', 'value'),
    Output('update-bartender-userform-employment-type', 'value'),
    Input('update-bartender-userform-bartender-id', 'value'),
    Input('update-bartender-userform-bartender-first-name', 'value'),
    Input('update-bartender-userform-bartender-last-name', 'value'),
    Input('update-bartender-userform-employment-type', 'value'),
    Input('update-bartender-userform-submit-entry', 'n_clicks')

)
def update_bartender_user_form(bartender_id, bartender_first_name, bartender_last_name, bartender_employment_type,
                               update_bartender_clicks):
    global update_bartender_n_of_clicks

    # If create bartender clicks is not None & the the local bartender clicks is greater than the global
    # value added number of drinks
    if update_bartender_clicks is not None and update_bartender_clicks > update_bartender_n_of_clicks:
        # Check to make sure it is not an empty form, we can do this by setting default value
        if bartender_id == '' or bartender_first_name == '' or bartender_last_name == '' or bartender_employment_type == '':
            update_bartender_n_of_clicks += 1  # Increase global clicks
            # Trigger complete the form error with no updates
            return True, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Database Update
        insert_tuple = (bartender_first_name, bartender_last_name, bartender_employment_type)
        sql_update = r'UPDATE Bartenders SET First_name="' + str(insert_tuple[0]) + r'", Last_name="' + str(insert_tuple[1]) + '", Employment_type=' + str(insert_tuple[2]) + ' WHERE Bartender_id=' + str(bartender_id) + ';'
        connection.non_query_statements(sql_update)

        update_bartender_n_of_clicks += 1  # Increase global counter by one
        return False, '', '', '', ''  # Clear user form
    else:
        raise PreventUpdate  # No update


@app.callback(
    Output('complete-all-information-error-update-value-added-drink', 'displayed'),
    Output('number-type-error-update-value-added-drink', 'displayed'),
    Output('existing-drink-update-value-added-drink', 'displayed'),
    Output('update-value-added-drink-userform-drink-id', 'value'),
    Output('update-value-added-drink-userform-drink-name', 'value'),
    Output('update-value-added-drink-userform-drink-bottle-size', 'value'),
    Output('update-value-added-drink-userform-drink-bottle-price', 'value'),
    Input('update-value-added-drink-userform-drink-id', 'value'),
    Input('update-value-added-drink-userform-drink-name', 'value'),
    Input('update-value-added-drink-userform-drink-bottle-size', 'value'),
    Input('update-value-added-drink-userform-drink-bottle-price', 'value'),
    Input('update-value-added-drink-userform-submit-entry', 'n_clicks')
)
def update_value_added_drink_user_form(value_added_drink_id, value_added_drink_name, value_added_bottle_size,
                                       value_added_bottle_price, update_value_added_clicks):
    global update_value_added_n_of_clicks

    # If create value added drinks is not None & the the local create value added clicks is greater than the global
    # value added number of drinks
    if update_value_added_clicks is not None and update_value_added_clicks > create_value_added_n_of_clicks:
        # If the inputs are empty throw error, we can do this with default errors
        if value_added_drink_id == '' or value_added_drink_name == '' or value_added_bottle_size == '' or value_added_bottle_price == '':
            update_value_added_n_of_clicks += 1  # Increase the global counter by one
            # Throw the complete the damn form error
            return True, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Attempt to float both bottle size & price to see if numbers
        try:
            value_added_bottle_size = float(value_added_bottle_size)
            value_added_bottle_price = float(value_added_bottle_price)
        except ValueError:
            update_value_added_n_of_clicks += 1  # Increase the global count by one
            # On error return the numeric error
            return True, False, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Test if drink already exists
        existing_drink_names = connection.query('SELECT Item_name FROM ItemSupplies;')['Item_name'].values.tolist()
        if value_added_drink_name in existing_drink_names:
            update_value_added_n_of_clicks += 1  # Increase the global clicks by one
            return False, False, True, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Database Updates
        insert_tuple = (value_added_drink_name, value_added_bottle_size, value_added_bottle_price)
        sql_update = r'UPDATE ItemSupplies SET Item_name="' + str(insert_tuple[0]) + r'", Item_size=' + str(
            insert_tuple[1]) + ', Item_price=' + str(insert_tuple[2]) + ' WHERE Item_id=' + str(
            value_added_drink_id) + ';'
        connection.non_query_statements(sql_update)

        update_value_added_n_of_clicks += 1  # Increase global counter by one
        return False, False, False, '', '', '', ''  # Clear Form
    else:
        raise PreventUpdate


# Delete Forms
@app.callback(
    Output('complete-all-information-error-delete-drink', 'displayed'),
    Output('delete-drink-userform-drink-name', 'value'),
    Input('delete-drink-userform-drink-name', 'value'),
    Input('delete-drink-userform-submit-entry', 'n_clicks')
)
def delete_drink_user_form(drink_name, delete_drink_clicks):
    global delete_drink_n_of_clicks

    # If delete drinks is not None & the the local delete drinks clicks is greater than the global
    # delete drinks
    if delete_drink_clicks is not None and delete_drink_clicks > delete_drink_n_of_clicks:
        if drink_name == '':
            delete_drink_n_of_clicks += 1  # Increase the global clicks
            # Throw complete user form error with no update
            return True, dash.no_update

        connection.non_query_statements('DELETE FROM OrderableItems WHERE Item_id=' + str(drink_name) + ';')
        delete_drink_n_of_clicks += 1
        return False, ''
    else:
        raise PreventUpdate


@app.callback(
    Output('complete-all-information-error-delete-bartender', 'displayed'),
    Output('delete-bartender-userform-bartender-name', 'value'),
    Input('delete-bartender-userform-bartender-name', 'value'),
    Input('delete-bartender-userform-submit-entry', 'n_clicks')
)
def delete_bartender_user_form(bartender_name, delete_bartender_clicks):
    global delete_bartender_n_of_clicks

    if delete_bartender_clicks is not None and delete_bartender_clicks > delete_bartender_n_of_clicks:
        if bartender_name == '':
            delete_bartender_n_of_clicks += 1
            return True, dash.no_update

        connection.non_query_statements('DELETE FROM Bartenders WHERE Bartender_id=' + str(bartender_name) + ';')
        delete_bartender_n_of_clicks += 1
        return False, ''
    else:
        raise PreventUpdate


@app.callback(
    Output('complete-all-information-error-delete-value-added-drink', 'displayed'),
    Output('delete-value-added-drink-userform-name', 'value'),
    Input('delete-value-added-drink-userform-name', 'value'),
    Input('delete-value-added-drink-userform-submit-entry', 'n_clicks')
)
def delete_value_added_drink_user_form(value_added_drink_name, delete_value_added_drink_clicks):
    global delete_value_added_n_of_clicks

    if delete_value_added_drink_clicks is not None and delete_value_added_drink_clicks > delete_value_added_n_of_clicks:
        if value_added_drink_name == '':
            delete_value_added_n_of_clicks += 1
            return True, dash.no_update

        connection.non_query_statements('DELETE FROM ItemSupplies WHERE Item_id=' + str(value_added_drink_name) + ';')
        delete_value_added_n_of_clicks += 1
        return False, ''
    else:
        raise PreventUpdate


# Run the application in debug mode for automatic updating
if __name__ == '__main__':
    app.run_server(debug=True)

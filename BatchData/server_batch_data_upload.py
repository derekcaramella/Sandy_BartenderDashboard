from ssh_tunnel import MySQLTunnel
import pandas as pd


host_name = 'derekcaramella.mysql.pythonanywhere-services.com'
username = 'derekcaramella'
password = 'PladisTurtles'
default_database = 'derekcaramella$dcaramel_1'

connection = MySQLTunnel(host_name, username, password, default_database)


def batch_insert(database_connection, dataframe, destination_table):
    staged_insert = str(dataframe.values.tolist()).replace('[', '(')
    staged_insert = staged_insert.replace(']', ')')
    staged_insert = staged_insert[1:-1]
    database_connection.non_query_statements('INSERT INTO ' + destination_table + ' VALUES ' + staged_insert + ';')
    return True


bartenders = pd.read_csv('Bartenders.csv')
item_supplies = pd.read_csv('ItemSupplies.csv')
orderable_items = pd.read_csv('OrderableItems.csv')
orders = pd.read_csv('Orders.csv', parse_dates=['Order Datetime'])
completed_orders = pd.read_csv('CompletedOrders.csv', parse_dates=['Completed Datetime'])
recipes = pd.read_csv('Recipes.csv')

batch_insert(connection, bartenders, 'Bartenders')
batch_insert(connection, item_supplies, 'ItemSupplies')
batch_insert(connection, orderable_items, 'OrderableItems')
batch_insert(connection, recipes, 'Recipes')
batch_insert(connection, orders, 'Orders')
batch_insert(connection, completed_orders, 'CompletedOrders')

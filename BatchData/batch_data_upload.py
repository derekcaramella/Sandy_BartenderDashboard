import ssh_tunnel
import pandas as pd


def batch_insert(database_connection, dataframe, destination_table):
    staged_insert = str(dataframe.values.tolist()).replace('[', '(')
    staged_insert = staged_insert.replace(']', ')')
    staged_insert = staged_insert[1:-1]
    database_connection.non_query_statements('INSERT INTO ' + destination_table + ' VALUES ' + staged_insert + ';')
    return True


host = 'betaweb.csug.rochester.edu'
port = 22
betaweb_username = 'dcaramel'
betaweb_password = 'PladisTurtles'
default_table = 'dcaramel_1'
local_host = '127.0.0.1'
local_port = 3306

connection = ssh_tunnel.MySQLTunnel(host, port, betaweb_username, betaweb_password, default_table, local_host,
                                    local_port)

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

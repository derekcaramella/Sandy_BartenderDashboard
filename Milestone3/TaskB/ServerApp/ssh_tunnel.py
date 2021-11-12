import mysql.connector as sq
import pandas as pd
import requests


class MySQLTunnel:
    """Since the database is hosted on a remote server, ssh tunneling is necessary to query the database"""

    def __init__(self, host, username, password, database_name, token):
        self.host = host
        self.username = username
        self.password = password
        self.database_name = database_name
        self.token = token

        try:
            self.connection, self.cursor = self.create_connection(self.host, self.username, self.password,
                                                                  self.database_name)
        except:
            self.reload_connection(self.username, self.token, self.host)
            self.connection, self.cursor = self.create_connection(self.host, self.username, self.password,
                                                                  self.database_name)

    def create_connection(self, host, username, pwd, database_name):
        # Create connection to database with the tunnel as the port
        connection = sq.connect(host=self.host,
                                user=self.username,
                                password=self.password,
                                database=self.database_name)
        cursor = connection.cursor()

        return connection, cursor

    def reload_connection(self, server_username, server_token, server_host):
        response = requests.get(
            'https://{host}/api/v0/user/{username}/cpu/'.format(
                host=server_host, username=server_username
            ),
            headers={'Authorization': 'Token {token}'.format(token=server_token)}
        )
        if response.status_code == 200:
            print('CPU quota info: ' + str(response.content))
            return True
        else:
            print('Got unexpected status code {}: {!r}'.format(response.status_code, response.content))
            return False

    def query(self, query):
        """Dataframe query. Does not include INSERT, UPDATE, & DELETE"""
        return pd.read_sql_query(query, self.connection)

    def non_query_statements(self, sql_statement):
        """SQL Statements not including select"""
        self.cursor.execute(sql_statement)
        self.connection.commit()
        return True

    def close_tunnel(self):
        """Close tunnel"""
        self.tunnel.close()
        return True

    def disconnect_sql(self):
        """Close MySql connection"""
        self.connection.close()
        return True

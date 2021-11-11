import mysql.connector as sq
import pandas as pd


class MySQLTunnel:
    """Since the database is hosted on a remote server, ssh tunneling is necessary to query the database"""

    def __init__(self, host, username, password, database_name):
        self.host = host
        self.username = username
        self.password = password
        self.database_name = database_name

        # Create connection to database with the tunnel as the port
        self.connection = sq.connect(host=self.host,
                                     user=self.username,
                                     password=self.password,
                                     database=self.database_name)
        self.cursor = self.connection.cursor()

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
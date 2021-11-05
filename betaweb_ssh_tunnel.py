# Import necessary modules
import pandas as pd
import pymysql
from sshtunnel import SSHTunnelForwarder


class MySQLTunnel:
    """Since the database is hosted on a remote server, ssh tunneling is necessary to query the database"""

    def __init__(self, ssh_host, ssh_port, ssh_username, ssh_password, database_name, local_host, local_port):
        self.ssh_host = ssh_host  # Initiate the ssh host name, follows the @ symbol
        self.ssh_port = ssh_port  # The ssh port usually 22
        self.ssh_username = ssh_username  # Initiate the ssh username, precedes the @ symbol
        self.ssh_password = ssh_password  # Initiate the ssh password, assumes db password is the same as login
        self.database_name = database_name  # Pass initial database connection
        self.local_host = local_host  # The local host IP address usually 127.0.0.1
        self.local_port = local_port  # The port usually 3306

        # Open an SSH tunnel and connect using a username and password.
        tunnel = SSHTunnelForwarder((self.ssh_host, self.ssh_port),
                                    ssh_username=self.ssh_username,
                                    ssh_password=self.ssh_password,
                                    remote_bind_address=(self.local_host, self.local_port))
        self.tunnel = tunnel
        tunnel.start()  # Start the tunnel

        # Create connection to database with the tunnel as the port
        connection = pymysql.connect(host=self.local_host,
                                     user=self.ssh_username,
                                     password=self.ssh_password,
                                     db=self.database_name,
                                     port=self.tunnel.local_bind_port,  # SSH Tunneling
                                     connect_timeout=6000)
        self.connection = connection  # Create connection attribute

    def query(self, query):
        """Dataframe query. Does not include INSERT, UPDATE, & DELETE"""
        return pd.read_sql_query(query, self.connection)

    def non_query_statements(self, sql_statement):
        """SQL Statements not including select"""
        self.connection.cursor().execute(sql_statement)
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

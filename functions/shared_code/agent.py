import pyodbc


class ConnectionAgent:

    def __init__(self, db_user: str, db_pass: str, db_host: str, port: int, db_name: str, db_driver: str):
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_host = db_host
        self.port = port
        self.db_name = db_name
        self.db_driver = db_driver

    @property
    def create_db_connection(self) -> pyodbc.Connection:
        """Creates db connections and returns a connection object.

        Returns:
            pyodbc.Connection: pyodbc connection object
        """
        cnxn = pyodbc.connect('DRIVER={' + self.db_driver + '};SERVER=' + self.db_host + ';\
                              DATABASE=' + self.db_name + ';UID=' + self.db_user + ';PWD=' + self.db_pass)
        return cnxn

    @property
    def create_connection_str(self) -> str:
        """Create a db connection string.

        Returns:
            str: pyodbc connection string.
        """
        conn_str = f'Server=tcp:{self.db_host},1433;Database={self.db_name};Uid={self.db_user};Pwd={self.db_pass};\
            Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        return conn_str

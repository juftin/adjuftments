#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Python Class File For Database Interactions.
"""

import logging
from os import getenv
from os.path import abspath, isfile
from pathlib import Path
from re import compile, sub

# noinspection PyUnresolvedReferences
from numpy import dtype, nan
from pandas import read_sql
from sqlalchemy import create_engine
# noinspection PyProtectedMember
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine.url import URL


class DatabaseError(Exception):
    """
    Generic Database Exception Error
    """
    pass


def get_conn_string(username: str = None,
                    password: str = None,
                    drivername: str = None,
                    host: str = None,
                    database: str = None,
                    port: int = None) -> URL:
    """
    Generate a SQLAlchemy Connection String Using Database Parameters.

    Parameters
    ----------
    username: str
        The database user name.
    password: str
        database password.
    drivername: str
        The name of the database backend.
        This name will correspond to a module in sqlalchemy/databases
        or a third party plug-in.
    host: str
        The name of the database host
    database: str
        The database name
    port: int
        The database port

    Returns
    -------
    connection_string: URL
        A formatted SQLAlchemy url.URL Connection String

    """
    if drivername is None:
        drivername = getenv("DATABASE_DRIVERNAME", default="postgresql+psycopg2")
    if host is None:
        host = getenv("DATABASE_HOST", default="redshift.prod.livongo.com")
    if database is None:
        database = getenv("DATABASE_DB", default="prod")
    if port is None:
        port = int(getenv("DATABASE_PORT", default="5439"))
    if username is None:
        username = getenv("DATABASE_USERNAME", default=None)
    if password is None:
        password = getenv("DATABASE_PASSWORD", default=None)
    for parameter in [username, password]:
        try:
            assert parameter is not None
        except AssertionError:
            error_message = ("Please provide a value for username or password, or set your "
                             "`DATABASE_USERNAME` and `DATABASE_PASSWORD` parameters.")
            logging.error(error_message)
            raise DatabaseError(error_message)
    connection_string = URL(drivername=drivername, username=username,
                            password=password,
                            host=host, port=port, database=database)
    return connection_string


def get_engine(username: str = None,
               password: str = None,
               drivername: str = None,
               host: str = None,
               database: str = None,
               port: int = None,
               keep_alive: bool = False) -> Engine:
    """
    Get a SQLAlchemy Engine. This function defaults to inheriting parameters from
    environment variables.

    Per the SQLAlchemy documentation: The Engine is intended to normally be a permanent fixture
    established up-front and maintained throughout the lifespan of an application. It is not
    intended to be created and disposed on a per-connection basis.

    Parameters
    ----------
    username: str
        The database user name.
    password: str
        database password.
    drivername: str
        The name of the database backend.
        This name will correspond to a module in sqlalchemy/databases
        or a third party plug-in.
    host: str
        The name of the database host
    database: str
        The database name
    port: int
        The database port
    keep_alive: bool
        Whether to keep the Engine alive

    Returns
    -------
    engine: Engine
        A SQLAlchemy Engine
    """
    connection_string = get_conn_string(drivername=drivername, username=username, password=password,
                                        host=host, port=port, database=database)
    if keep_alive is True:
        keep_alive_kwargs = {"connect_args": {"keepalives": 1,
                                              "keepalives_idle": 60,
                                              "keepalives_interval": 60}}
    elif keep_alive is False:
        keep_alive_kwargs = dict()
    engine = create_engine(connection_string,
                           execution_options={"autocommit": True},
                           encoding="utf-8",
                           isolation_level="AUTOCOMMIT",
                           pool_pre_ping=False,
                           **keep_alive_kwargs)
    return engine


def get_connection(username: str = None,
                   password: str = None,
                   drivername: str = None,
                   host: str = None,
                   database: str = None,
                   port: int = None,
                   keep_alive: bool = False) -> Connection:
    """
    Get a SQLAlchemy Database connection. This function defaults to inheriting parameters from
    environment variables.

    Per the SQLAlchemy documentation: The Connection object represents a single dbapi connection
    checked out from the connection pool. In this state, the connection pool has no affect upon
    the connection, including its expiration or timeout state. For the connection pool to
    properly manage connections, connections should be returned to the connection pool
    (i.e. connection.close()) whenever the connection is not in use.

    Parameters
    ----------
    username: str
        The database user name.
    password: str
        database password.
    drivername: str
        The name of the database backend.
        This name will correspond to a module in sqlalchemy/databases
        or a third party plug-in.
    host: str
        The name of the database host
    database: str
        The database name
    port: int
        The database port
    keep_alive: bool
        Whether to keep the Engine alive

    Returns
    -------
    connection: Connection
        An active SQLAlchemy Connection
    """
    engine = get_engine(drivername=drivername, username=username, password=password,
                        host=host, port=port, database=database, keep_alive=keep_alive)
    connection = engine.connect()
    return connection


class DatabaseConnection(object):
    """
    A database connection object.
    """

    def __init__(self,
                 username: str = None,
                 password: str = None,
                 drivername: str = None,
                 host: str = None,
                 database: str = None,
                 port: int = None,
                 keep_alive: bool = False):
        """
        Parameters
        ----------
        username: str
            The database user name.
        password: str
            database password.
        drivername: str
            The name of the database backend.
            This name will correspond to a module in sqlalchemy/databases
            or a third party plug-in.
        host: str
            The name of the database host
        database: str
            The database name
        port: int
            The database port
        keep_alive: bool
            Whether to keep the Engine alive
        """
        self.engine = get_engine(drivername=drivername, username=username, password=password,
                                 host=host, port=port, database=database, keep_alive=keep_alive)
        self.host = self.engine.url.host
        self.db_connection = False
        self.sql_conn = None

    def __repr__(self):
        return f"( database.Connection: {self.host} )"

    def db_connect(self):
        """
        Create a Database Connection.
        """
        if not self.db_connection:
            self.sql_conn = self.engine.connect()
            logging.debug(f"\tDatabase Connection opened: {self.host}")
            self.db_connection = True

    def db_disconnect(self):
        """
        Close a Database Connection.
        """
        if self.db_connection:
            self.sql_conn.close()
            logging.debug(f"\tDatabase Connection closed: {self.host}")
            self.db_connection = False

    def execute(self, statement: str) -> str:
        """
        Execute a SQL Transaction

        Parameters
        ----------
        statement: str
            SQL Execution Statement

        Returns
        -------
        response: str
            Database response to the Execution
        """
        self.db_connect()
        database_response = self.sql_conn.execute(statement)
        self.db_disconnect()
        return database_response

    @staticmethod
    def format_sql(query: str, query_format_dict: dict) -> str:
        """
        Format a SQL Query string using a dictionary.

        Parameters
        ----------
        query: str
            Raw text of SQL query with format placeholders
        query_format_dict: str
            A dictionary of format keys and values

        Returns
        -------
        formatted_query: str
            A formatted SQL query
        """
        formatted_query = query.format(**query_format_dict)
        return formatted_query

    @staticmethod
    def read_sql_file(file_path, query_format_dict: dict = None):
        """
        Ingest a .sql file and return its raw text.

        Parameters
        ----------
        file_path: str
            File path of .sql file
        query_format_dict: dict
            A dictionary of format keys and values

        Returns
        -------
        raw_query: str
            Text contained within .sql file
        """
        file_path = Path(abspath(file_path))
        with open(file_path, "r", encoding="utf-8") as r:
            raw_query = r.read()
        if query_format_dict is not None:
            raw_query = DatabaseConnection.format_sql(query=raw_query,
                                                      query_format_dict=query_format_dict)
        return raw_query

    def sql_to_df(self, sql: str, query_format_dict: dict = None):
        """
        Execute a query from file or stream and return a Pandas dataframe.

        Any {keys} contained in the query that aren't addressed with the
        format dictionary will be populated with "1 = 1"

        Parameters
        ----------
        sql: str
            a file path of .sql file or raw text of SQL query

        query_format_dict: dict
            a dictionary that populates any keys formatted: {key}
            with it's corresponding value

        Returns
        -------
        dataframe: pd.DataFrame
            assembled dataframe from SQL query
        """
        self.db_connect()
        if isfile(sql):
            query = DatabaseConnection.read_sql_file(file_path=sql,
                                                     query_format_dict=query_format_dict)
        else:
            query = sql
        if query_format_dict:
            query = DatabaseConnection.format_sql(query=query, query_format_dict=query_format_dict)
        regex_match = compile(r"{(.*)}")
        query = sub(pattern=regex_match, string=query, repl="1 = 1")
        dataframe = read_sql(sql=query, con=self.sql_conn)
        self.db_disconnect()
        return dataframe

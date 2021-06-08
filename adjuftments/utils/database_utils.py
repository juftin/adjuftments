#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Interactions with Postgres Database
"""

import logging
from os import getenv
from typing import Optional

from sqlalchemy import create_engine
# noinspection PyProtectedMember
from sqlalchemy.engine import Connection, Engine, ResultProxy  # Protected members used for Typing
from sqlalchemy.engine.url import URL

logger = logging.getLogger(__name__)


class DatabaseConnectionUtils(object):
    """
    Connection Base Class
    """

    def __init__(self, username: str = None,
                 password: str = None,
                 drivername: str = None,
                 host: str = None,
                 database: str = None,
                 port: int = None):
        """
        At the root of every unload is a SQL Statement

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
        """
        self.engine: Engine = self.get_engine(drivername=drivername,
                                              username=username,
                                              password=password,
                                              host=host,
                                              port=port,
                                              database=database)
        self.database_connection: Optional[Connection] = None
        self.connected: bool = False

    def __repr__(self) -> str:
        """
        String Representation
        """
        return f"<DatabaseConnection: {self.engine.url.host}>"

    def execute(self, statement: str) -> ResultProxy:
        """
        Execute a SQL Statement against the Database
        Parameters
        ----------
        statement: str
            SQL Statement to Execute
        Returns
        -------
        ResultProxy
        """
        if self.connected is False:
            self._connect()
        database_response = self.database_connection.execute(statement)
        return database_response

    @staticmethod
    def get_connection_string(username: str = None,
                              password: str = None,
                              drivername: str = None,
                              host: str = None,
                              database: str = None,
                              port: int = None) -> URL:
        """
        Generate a SQLAlchemy Connection String Using Database Parameters. Default to
        Environment Variables
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
            host = getenv("DATABASE_HOST", default=None)
        if database is None:
            database = getenv("DATABASE_DB", default=None)
        if port is None:
            port = int(getenv("DATABASE_PORT", default="5432"))
        if username is None:
            username = getenv("DATABASE_USERNAME", default=None)
        if password is None:
            password = getenv("DATABASE_PASSWORD", default=None)
        for parameter in [host, username, password]:
            try:
                assert parameter is not None
            except AssertionError:
                mandatory_environment_variables = ["DATABASE_HOST",
                                                   "DATABASE_DB",
                                                   "DATABASE_USERNAME",
                                                   "DATABASE_PASSWORD"]
                env_var_string = "\n".join(["\t" + var for var in mandatory_environment_variables])
                error_message = ("Please provide a value for host, username, and password, "
                                 f"or set your environment variables: \n{env_var_string}")
                logging.error(error_message)
                raise EnvironmentError(error_message)
        connection_string = URL(drivername=drivername, username=username,
                                password=password,
                                host=host, port=port, database=database)
        return connection_string

    @staticmethod
    def get_engine(username: str = None,
                   password: str = None,
                   drivername: str = None,
                   host: str = None,
                   database: str = None,
                   port: int = None,
                   keep_alive: bool = True,
                   autocommit: bool = True) -> Engine:
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
        autocommit: bool
            Whether to AUTOCOMMIT everything
        Returns
        -------
        engine: Engine
            A SQLAlchemy Engine
        """
        connection_string = DatabaseConnectionUtils.get_connection_string(drivername=drivername,
                                                                          username=username,
                                                                          password=password,
                                                                          host=host, port=port,
                                                                          database=database)
        if keep_alive is True:
            keep_alive_kwargs = {"connect_args": {"keepalives": 1,
                                                  "keepalives_idle": 60,
                                                  "keepalives_interval": 60}}
        else:
            keep_alive_kwargs = dict()
        if autocommit is True:
            autocommit_kwargs = dict(execution_options={"autocommit": True},
                                     isolation_level="AUTOCOMMIT")
        else:
            autocommit_kwargs = dict(execution_options={"autocommit": False})
        engine = create_engine(connection_string,
                               encoding="utf-8",
                               pool_pre_ping=False,
                               **autocommit_kwargs,
                               **keep_alive_kwargs)
        return engine

    def _connect(self) -> Connection:
        """
        Connect to the Database
        Returns
        -------
        Connection
        """
        if self.connected is False:
            logger.info("Opening database connection")
            connection = self.engine.connect()
            self.database_connection = connection
            self.connected = True
            logger.info("Database Connected")
            return connection

    def _disconnect(self) -> None:
        """
        Connect to the Database
        Returns
        -------
        Connection
        """
        if self.connected is True:
            logger.info("Closing database connection")
            self.database_connection.close()
            self.database_connection = None
            self.connected = False
            logger.info("Database connection closed")

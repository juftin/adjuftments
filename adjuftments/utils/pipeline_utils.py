#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Pipeline Utilities for Adjuftments
"""

from datetime import datetime
import logging
from sys import exc_info
from time import sleep
from typing import Callable, List, Optional

from .error_utils import AdjuftmentsRefreshError

logger = logging.getLogger(__name__)


def capture_error(log_error: bool = True):
    """
    Capture an Error and Log it

    Parameters:
    --------------
    log_error: bool
        Whether to log the error message
    """
    exc_type, exc_value, exc_traceback = exc_info()
    error_message = "{0}: {1}".format(exc_type.__name__, exc_value)
    if log_error is True:
        logging.error(error_message)
    return error_message


def run_adjuftments_refresh_pipeline(sleep_config: List[int],
                                     primary_function: Callable,
                                     finally_function: Optional[Callable] = None,
                                     error_index: Optional[int] = None,
                                     catchable_error: Exception = BaseException,
                                     between_loops_sleep: int = 30,
                                     **kwargs) -> None:
    """
    Run the Pipeline - Which is fault tolerant up until a point

    Parameters
    ----------
    sleep_config: List[int]
        List of sequential times to sleep between consecutive errors
    primary_function: Callable
        Callable object to be run (accepts **kwargs)
    finally_function: Optional[Callable]
        Callable object to be run- accepts the returned value from primary function
    error_index: Optional[int]
        Optional index on the sleep_config list to begin throwing ERROR log events
        instead of WARNING log events
    catchable_error: BaseException
        Exception to catch
    between_loops_sleep: int
        Number of seconds to wait in between loops
    **kwargs
        Passed to primary_function

    Returns
    -------
    None
    """
    assert catchable_error is not AdjuftmentsRefreshError
    # CREATE AN EMPTY ATTEMPTS LIST AND ADD A FINAL SLEEP OF 0 TO SLEEP CONFIG
    retry_attempts = list()
    pipeline_start_time = datetime.now()
    while True:
        # CAPTURE SOME IMPORTANT INFO AT THE BEGINNING OF EACH LOOP
        loop_start_time = datetime.now()
        number_retry_attempts = len(retry_attempts)
        sleep_config_size = len(sleep_config)
        # noinspection PyBroadException
        try:
            # IF RUNS HAVEN'T BEEN EXHAUSTED
            if number_retry_attempts <= sleep_config_size:
                # EXECUTE THE PRIMARY FUNCTION AND APPEND TO *ARGS FOR SECONDARY
                returned_value = primary_function(**kwargs)
                # CLEAR THE RETRY ATTEMPTS IF SUCCESSFUL RUN
                retry_attempts.clear()
            else:
                # ONCE ATTEMPTS HAVE BEEN EXHAUSTED, LOG AN ERROR AND QUIT
                error_message = f"Retry Attempts Exhausted: {number_retry_attempts}"
                logger.error(error_message)
                raise AdjuftmentsRefreshError(error_message)
        # HANDLE EXCEPTIONS
        except catchable_error:
            # CAPTURE AN ERROR AND APPROPRIATELY LOG IT
            error_type = capture_error(log_error=False)
            error_message = (f"Handled Exception: {error_type}.\n"
                             f"Retry Attempts: {number_retry_attempts}")
            if error_index <= number_retry_attempts < sleep_config_size:
                logger.error(error_message)
            elif number_retry_attempts < sleep_config_size:
                logger.warning(error_message)
            # RUN THE SUB COMMAND TO UPDATE THE RETRY ATTEMPTS
            retry_attempts = _sub_refresh_assist(sleep_config=sleep_config,
                                                 retry_attempts=retry_attempts)
        # RUN THE FINALLY FUNCTION WITH *ARGS FROM PRIMARY
        finally:
            if finally_function is not None:
                finally_function(*returned_value)
            # RECORD LOOP TIME
            loop_end_time = datetime.now()
            logger.info(f"Adjuftments Refresh Loop Completed: {loop_end_time - loop_start_time}. "
                        f"Uptime: {loop_end_time - pipeline_start_time}")
            sleep(between_loops_sleep)


def _sub_refresh_assist(sleep_config: List[int],
                        retry_attempts: list) -> int:
    """
    Assist with with the retry attempts parameter for run_adjuftments_refresh.
    Returns a new retry_events object

    Parameters
    ----------
    sleep_config: List[int]
        List of sequential times to sleep between consecutive errors
    retry_attempts: list
        List of preceding retry attempts

    Returns
    -------
    int
    """
    try:
        # GET THE TIME TO SLEEP AND APPROPRIATELY LOG IT
        time_to_sleep = sleep_config[len(retry_attempts)]
        logging_statement = ("Refresh loop will be skipped due to an underlying issue. "
                             f"Waiting {time_to_sleep} seconds.")
        logger.warning(logging_statement)
        sleep(time_to_sleep)
    # HANDLE SITUATIONS WHERE RETRY ATTEMPTS ARE EXHAUSTED
    except IndexError:
        time_to_sleep = "Forever!"
    finally:
        retry_attempts.append(time_to_sleep)
    return retry_attempts

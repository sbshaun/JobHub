import json
import logging
import traceback
from typing import Any, Dict, Optional

# Config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def error(function_name: str, sub_function_name: str, exception: Exception, additional_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error message.

    :param function_name: Name of the main function where the error occurred.
    :param sub_function_name: Name of the subfunction where the error occurred.
    :param exception: The exception object caught.
    :param additional_info: Optional dictionary with additional context 
    """
    error_info = {
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "function_name": function_name,
        "sub_function_name": sub_function_name,
        "stack_trace": traceback.format_exc()
    }

    if additional_info:
        error_info["additional_info"] = additional_info

    logger.error(json.dumps(error_info))

def success(function_name: str, message: str, additional_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a success message.

    :param function_name: Name of the function logging the success message.
    :param message: Success message.
    :param additional_info: Optional dictionary with additional context.
    """
    log_info = {
        "function_name": function_name,
        "message": message
    }

    if additional_info:
        log_info["additional_info"] = additional_info

    logger.info(json.dumps(log_info))

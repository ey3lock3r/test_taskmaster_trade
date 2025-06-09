import logging

def setup_logging(log_level_str: str):
    """
    Sets up the logging configuration for the application.
    Logs to console and a file.
    """
    log_level = log_level_str.upper()
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Create logger
    logger = logging.getLogger("algotrader")
    logger.setLevel(numeric_level)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)

    # Create file handler
    fh = logging.FileHandler("algotrader.log")
    fh.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add formatter to handlers
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

# Initialize logger
logger = logging.getLogger("algotrader") # Initialize a basic logger first
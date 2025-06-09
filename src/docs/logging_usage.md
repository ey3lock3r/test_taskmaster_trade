# Logging Usage and Maintenance

This document outlines the usage, configuration, and maintenance procedures for the application's logging system.

## 1. Logging Levels

The application uses standard Python logging levels to categorize messages:

-   **DEBUG**: Detailed information, typically of interest only when diagnosing problems. This includes internal state, verbose data, and step-by-step calculations.
-   **INFO**: Confirmation that things are working as expected. This includes bot start/stop events, successful configuration/data fetches, and successful order actions.
-   **WARNING**: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., 'disk space low'). The software is still working as expected. This includes minor API issues, non-critical data inconsistencies, or strategy adjustments.
-   **ERROR**: Due to a more serious problem, the software has not been able to perform some function. This includes failed API calls, database errors, or critical calculation failures.
-   **CRITICAL**: A serious error, indicating that the program itself may be unable to continue running. This includes unhandled exceptions or severe system resource issues.

## 2. Configuration

The logging system is configured in [`src/utils/logger.py`](src/utils/logger.py) and uses settings from [`src/config.py`](src/config.py).

To adjust the global logging level:

1.  Open [`src/config.py`](src/config.py).
2.  Modify the `log_level` variable in the `Settings` class to your desired level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").

    ```python
    # src/config.py
    class Settings(BaseSettings):
        # ... other settings
        log_level: str = "INFO" # Change this value
        # ...
    ```

3.  Restart the application for changes to take effect.

## 3. Log File Management

Logs are written to `algotrader.log` in the root directory of the application.

-   **Location**: `algotrader.log`
-   **Rotation**: Currently, log rotation is not explicitly configured. For long-running deployments, consider implementing log rotation (e.g., using `logging.handlers.RotatingFileHandler` or external tools like `logrotate`) to prevent log files from growing indefinitely.

## 4. Troubleshooting

-   **No logs appearing**:
    -   Ensure the `log_level` in `src/config.py` is set appropriately (e.g., "DEBUG" to see all messages).
    -   Check file permissions for `algotrader.log` in the application's root directory.
-   **Missing specific events**:
    -   Verify that logging calls (`logger.info()`, `logger.debug()`, etc.) are present in the relevant code sections.
    -   Check the log level set for the specific logger instance in `src/utils/logger.py`.

## 5. Integration Examples

Here's how logging is integrated into the application:

```python
# Example from src/api/middleware.py
import logging
logger = logging.getLogger(__name__)

# ...
logger.debug(f"AuthMiddleware: Processing request for path: {request.url.path}, token: {token}")
# ...
logging.exception(f"Unhandled exception in AuthMiddleware: {e}")
```

```python
# Example from src/api/routes.py
import logging
logger = logging.getLogger(__name__)

# ...
logger.info(f"Attempting to register new user: {user.username}")
# ...
logger.warning(f"Registration failed: Username '{user.username}' already registered.")
# ...
logger.error(f"Refresh token verification failed: {e}", exc_info=True)
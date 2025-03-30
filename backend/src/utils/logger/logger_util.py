import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from src.settings import BackendBaseSettings

class RootLoggerConfig(BackendBaseSettings):
    def __init__(self):
        """
        Configures the root logger for the entire application.
        """
        super().__init__()
        self._configure_root_logger()

    def _configure_root_logger(self):
        """
        Configures the root logger with console and file handlers.
        """
        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.LOG_LEVEL)

        # Clear existing handlers to avoid duplication
        self._clear_existing_handlers(root_logger)

        # Create and add handlers
        self._add_console_handler(root_logger)
        self._add_file_handler(root_logger)

    def _clear_existing_handlers(self, logger: logging.Logger):
        """
        Removes all existing handlers from the logger.
        
        Args:
            logger (logging.Logger): The logger instance to clear handlers from.
        """
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    def _add_console_handler(self, logger: logging.Logger):
        """
        Adds a console handler to the logger.
        
        Args:
            logger (logging.Logger): The logger instance to add the handler to.
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._create_formatter())
        logger.addHandler(console_handler)

    def _add_file_handler(self, logger: logging.Logger):
        """
        Adds a file handler with log rotation to the logger.
        
        Args:
            logger (logging.Logger): The logger instance to add the handler to.
        """
        file_handler = TimedRotatingFileHandler(
            filename=self.LOG_FILE,
            when="midnight",
            backupCount=self.BACKUP,
            encoding="utf-8"
        )
        file_handler.setFormatter(self._create_formatter())
        logger.addHandler(file_handler)

    def _create_formatter(self) -> logging.Formatter:
        """
        Creates a logging formatter with the configured format and date format.
        
        Returns:
            logging.Formatter: The configured formatter.
        """
        return logging.Formatter(
            fmt=self.LOG_FORMAT,
            datefmt=self.DATE_FORMAT
        )
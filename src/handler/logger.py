"""
Logging Handler Module
======================

Provides comprehensive logging functionality with file rotation, 
multiple handlers, and customizable formatting using colorama.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colorama support for console output.
    
    Attributes
    ----------
    COLORS : dict
        Mapping of log levels to colorama color codes.
    """
    
    # Colorama color mapping
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
    }
    
    def format(self, record):
        """
        Format log record with colors using colorama.
        
        Parameters
        ----------
        record : logging.LogRecord
            The log record to format.
            
        Returns
        -------
        str
            Formatted log message with color codes.
        """
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        record.msg = f"{log_color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)


class LoggerManager:
    """
    Centralized logger management with file and console handlers.
    
    Supports log rotation, custom formatting, and multiple log levels.
    
    Parameters
    ----------
    name : str, optional
        Logger name, by default "app"
    log_dir : str, optional
        Directory for log files, by default "logs"
    log_level : int, optional
        Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL), 
        by default logging.INFO
    console_output : bool, optional
        Enable console output, by default True
    file_output : bool, optional
        Enable file output, by default True
    max_bytes : int, optional
        Maximum size of log file before rotation, by default 10MB
    backup_count : int, optional
        Number of backup files to keep, by default 5
    log_format : str or None, optional
        Custom log format string, by default None
    date_format : str or None, optional
        Custom date format string, by default None
        
    Attributes
    ----------
    logger : logging.Logger
        The configured logger instance.
    """
    
    def __init__(
        self,
        name: str = "app",
        log_dir: str = "logs",
        log_level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None
    ):
        """
        Initialize the logger manager.
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.console_output = console_output
        self.file_output = file_output
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Default formats
        self.log_format = log_format or (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
        self.date_format = date_format or "%Y-%m-%d %H:%M:%S"
        
        # Create logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Setup and configure the logger with handlers.
        
        Returns
        -------
        logging.Logger
            Configured logger instance.
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        logger.handlers.clear()  # Clear existing handlers
        
        # Console handler with colors
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = ColoredFormatter(
                self.log_format,
                datefmt=self.date_format
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.file_output:
            self._create_log_directory()
            
            # Main log file
            log_file = self.log_dir / f"{self.name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_formatter = logging.Formatter(
                self.log_format,
                datefmt=self.date_format
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Error log file (only ERROR and CRITICAL)
            error_log_file = self.log_dir / f"{self.name}_error.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            logger.addHandler(error_handler)
        
        return logger
    
    def _create_log_directory(self):
        """Create log directory if it doesn't exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.
        
        Returns
        -------
        logging.Logger
            The configured logger instance.
        """
        return self.logger
    
    def set_level(self, level: int):
        """
        Change the logging level.
        
        Parameters
        ----------
        level : int
            New logging level (e.g., logging.DEBUG, logging.INFO).
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)
    
    def add_file_handler(
        self,
        filename: str,
        level: int = logging.INFO,
        formatter: Optional[logging.Formatter] = None
    ):
        """
        Add an additional file handler.
        
        Parameters
        ----------
        filename : str
            Name of the log file.
        level : int, optional
            Logging level for this handler, by default logging.INFO.
        formatter : logging.Formatter or None, optional
            Custom formatter (uses default if None), by default None.
        """
        log_file = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        
        if formatter is None:
            formatter = logging.Formatter(
                self.log_format,
                datefmt=self.date_format
            )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


# Global logger instance
_default_logger: Optional[LoggerManager] = None


def setup_logging(
    name: str = "app",
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
    **kwargs
) -> logging.Logger:
    """
    Setup and return a configured logger.
    
    Parameters
    ----------
    name : str, optional
        Logger name, by default "app"
    log_dir : str, optional
        Directory for log files, by default "logs"
    log_level : int, optional
        Minimum log level, by default logging.INFO
    console_output : bool, optional
        Enable console output, by default True
    file_output : bool, optional
        Enable file output, by default True
    **kwargs : dict
        Additional arguments for LoggerManager
    
    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    global _default_logger
    _default_logger = LoggerManager(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output,
        file_output=file_output,
        **kwargs
    )
    return _default_logger.get_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Parameters
    ----------
    name : str or None, optional
        Logger name (uses default if None), by default None
    
    Returns
    -------
    logging.Logger
        Logger instance.
    """
    if name is None and _default_logger is not None:
        return _default_logger.get_logger()
    return logging.getLogger(name or "app")


# Convenience functions
def debug(msg: str, *args, **kwargs):
    """
    Log a debug message.
    
    Parameters
    ----------
    msg : str
        The message to log.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.
    """
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """
    Log an info message.
    
    Parameters
    ----------
    msg : str
        The message to log.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.
    """
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """
    Log a warning message.
    
    Parameters
    ----------
    msg : str
        The message to log.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.
    """
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """
    Log an error message.
    
    Parameters
    ----------
    msg : str
        The message to log.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.
    """
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """
    Log a critical message.
    
    Parameters
    ----------
    msg : str
        The message to log.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.
    """
    get_logger().critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """
    Log an exception with traceback.
    
    Parameters
    ----------
    msg : str
        The message to log.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.
    """
    get_logger().exception(msg, *args, **kwargs)


# Example usage
if __name__ == "__main__":
    # Setup logging
    logger = setup_logging(
        name="my_app",
        log_level=logging.DEBUG,
        console_output=True,
        file_output=True
    )
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        result = 1 / 0
    except ZeroDivisionError:
        logger.exception("An error occurred during division")
    
    # Using convenience functions
    info("Application started successfully")
    debug(f"Current timestamp: {datetime.now()}")
    warning("This is a warning using convenience function")
    
    print(f"\n{Fore.GREEN}Logs saved to: {Path('logs').absolute()}{Style.RESET_ALL}")
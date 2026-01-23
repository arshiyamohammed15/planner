"""
Automatic error logging system.
Captures all errors and exceptions, storing them in errors.log file.
"""

from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Error log file path
ERROR_LOG_FILE = Path(__file__).parent / "errors.log"


class ErrorLogger:
    """
    Automatic error logger that captures all errors to errors.log file.
    """

    def __init__(self, log_file: Path = ERROR_LOG_FILE):
        self.log_file = log_file
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure logger to write only errors to file."""
        logger = logging.getLogger("planner_agent_errors")
        logger.setLevel(logging.ERROR)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # File handler for errors only
        file_handler = logging.FileHandler(
            self.log_file,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.ERROR)
        
        # Format: timestamp, level, message, traceback
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger

    def log_error(
        self,
        error: Exception | str,
        context: Optional[dict[str, Any]] = None,
        exc_info: Optional[tuple] = None
    ) -> None:
        """
        Log an error to the errors.log file.
        
        Args:
            error: Exception instance or error message string
            context: Optional context dictionary with additional info
            exc_info: Optional exception info tuple (from sys.exc_info())
        """
        try:
            error_message = str(error) if isinstance(error, Exception) else str(error)
            
            # Build log message
            log_msg = f"ERROR: {error_message}"
            if context:
                context_str = ", ".join(f"{k}={v}" for k, v in context.items())
                log_msg += f" | Context: {context_str}"
            
            # Log with exception info if available
            if exc_info:
                self.logger.error(log_msg, exc_info=exc_info)
            elif isinstance(error, Exception):
                self.logger.error(log_msg, exc_info=(type(error), error, error.__traceback__))
            else:
                self.logger.error(log_msg)
                
        except Exception as log_error:
            # Fallback: write directly to file if logger fails
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"{timestamp} - CRITICAL - Failed to log error: {log_error}\n")
                    f.write(f"Original error: {error}\n")
                    if context:
                        f.write(f"Context: {context}\n")
                    f.write(f"{traceback.format_exc()}\n\n")
            except Exception:
                # Last resort: print to stderr
                print(f"CRITICAL: Cannot write to error log. Error: {error}", file=sys.stderr)

    def log_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: Any,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Log an exception with full traceback.
        
        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object
            context: Optional context dictionary
        """
        self.log_error(
            exc_value,
            context=context,
            exc_info=(exc_type, exc_value, exc_traceback)
        )


# Global error logger instance
_error_logger = ErrorLogger()


def log_error(error: Exception | str, context: Optional[dict[str, Any]] = None) -> None:
    """
    Convenience function to log an error.
    
    Args:
        error: Exception or error message
        context: Optional context information
    """
    _error_logger.log_error(error, context=context)


def setup_exception_handler() -> None:
    """Set up global exception handler to capture all unhandled exceptions."""
    def exception_handler(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
        """Global exception handler."""
        if exc_type is KeyboardInterrupt:
            # Don't log keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        _error_logger.log_exception(exc_type, exc_value, exc_traceback)
        
        # Call default exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # Set as global exception handler
    sys.excepthook = exception_handler


def setup_stderr_capture() -> None:
    """Capture stderr output and log errors."""
    class ErrorCapture:
        """Capture stderr and log errors."""
        
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
        
        def write(self, text: str) -> None:
            """Write to both original stderr and error log."""
            if text.strip():  # Only log non-empty lines
                # Check if it looks like an error
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ['error', 'exception', 'traceback', 'failed', 'fatal']):
                    try:
                        _error_logger.log_error(text.strip())
                    except Exception:
                        pass
            
            # Also write to original stderr
            self.original_stderr.write(text)
        
        def flush(self) -> None:
            """Flush original stderr."""
            self.original_stderr.flush()
    
    # Replace stderr with our capture
    sys.stderr = ErrorCapture(sys.stderr)


__all__ = [
    "ErrorLogger",
    "log_error",
    "setup_exception_handler",
    "setup_stderr_capture",
    "ERROR_LOG_FILE",
]


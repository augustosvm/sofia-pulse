#!/usr/bin/env python3
"""
Sofia Pulse - Professional Logger
Centralized logging for all collectors
"""

import logging
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("/var/log/sofia/collectors")

def setup_logger(name, log_file=None):
    """
    Setup professional logger for collector

    Args:
        name: Logger name (e.g., 'collect-github')
        log_file: Optional custom log file path

    Returns:
        Logger instance
    """
    # Create log directory if it doesn't exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Default log file based on name
    if log_file is None:
        log_file = LOG_DIR / f"{name}.log"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler (detailed logs)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler (important info only)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_collector_start(logger, collector_name):
    """Log collector start with separator"""
    logger.info("="*70)
    logger.info(f"START: {collector_name}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)

def log_collector_finish(logger, collector_name, rows_inserted, duration_seconds):
    """Log collector completion"""
    logger.info("="*70)
    logger.info(f"FINISHED: {collector_name}")
    logger.info(f"Rows inserted: {rows_inserted}")
    logger.info(f"Duration: {duration_seconds:.2f}s")
    logger.info(f"Status: SUCCESS")
    logger.info("="*70)

def log_collector_error(logger, collector_name, error, duration_seconds=None):
    """Log collector error"""
    logger.error("="*70)
    logger.error(f"FAILED: {collector_name}")
    logger.error(f"Error: {error}")
    if duration_seconds:
        logger.error(f"Failed after: {duration_seconds:.2f}s")
    logger.error(f"Status: FAILED")
    logger.error("="*70)

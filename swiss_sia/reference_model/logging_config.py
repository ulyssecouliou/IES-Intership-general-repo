"""Logging configuration suitable for the VE Scripts output pane and files."""

import logging
from pathlib import Path
from typing import Union


LOGGER_NAME = "swiss_sia.reference_model"


def configure_logging(output_folder: Union[str, Path]) -> logging.Logger:
    """Configure shared console and UTF-8 file logging once."""

    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(
        str(output_path / "reference_model.log"), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger

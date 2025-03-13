import logging
import os

# Configure logging
logging_level = os.environ.get("LOGGING_LEVEL", "INFO")
numeric_level = getattr(logging, logging_level, logging.INFO)

logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
import logging
import os
import sys


class Config():
    teams_url = os.getenv('TEAMS_URL')
    namespace = os.getenv('NAMESPACE')
    label = os.getenv('LABEL')
    interval = float(os.getenv('INTERVAL', 30))
    
    # Logging
    @staticmethod
    def setup_logging():
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_level = getattr(logging, log_level.upper())
        
        # Create a logger
        logger = logging.getLogger()
        logger.setLevel(log_level)

        # Create a stream handler that outputs to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        # Create a formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

        return logger
    
    @staticmethod
    def cluster():
        """Name of the cluster"""
        return os.getenv('CLUSTER_NAME')
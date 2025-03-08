import logging


class Logger():
    def __init__(self,logFile):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[
            logging.FileHandler(logFile),
            logging.StreamHandler()
        ])

    def print(self,msg):
        print(msg)
        logging.info(msg)
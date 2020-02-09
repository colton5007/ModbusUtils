import logging

logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename='ss.log',
                        filemode='w')


def setup(logger_name):
    logger = logging.getLogger(logger_name)
    return logger

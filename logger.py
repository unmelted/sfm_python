import logging
from datetime import datetime
from logging.handlers import SocketHandler


class Logger(object) :
    instance = None
    
    @staticmethod
    def get() :
        if Logger.instance is None:
            Logger.instance = Logger()
        return Logger.instance

    def __init__ (self, type, ip='127.0.0.1') :
        w = logging.getLogger('calib')
        w.basicConfig(level=logging.INFO, format='%(asctime)s : %(levelname)s : %(name)s : %(module)s : %(message)s')

        if 'file' in type:
            now = datetime.now()
            logname = datetime.strftime(now, '%Y%M%D_Calib') + '.txt'
            file_handler = logging.FileHandler(logname)
            w.addHandler(file_handler)

        if 'viewer' in type:
            socket_handler = SocketHandler(ip, 19996)  # default listening address
            w.addHandler(socket_handler)


            # log.info('Hello world!')
            



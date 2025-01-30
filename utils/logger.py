import logging
from logging.handlers import TimedRotatingFileHandler

# Configurar el logger con TimedRotatingFileHandler
log_file_name = 'server_log'
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Crear el manejador rotativo por día
handler = TimedRotatingFileHandler(filename=f'{log_file_name}.log', when="midnight", interval=1, backupCount=5)
handler.setFormatter(log_formatter)

# Configurar el logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
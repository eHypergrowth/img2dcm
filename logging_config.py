import logging
import os
from logging.handlers import RotatingFileHandler

# Crear el directorio "logs" si no existe
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar el archivo de logs dentro de la carpeta "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configurar rotación de logs
rotating_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5  # Tamaño máximo de 5 MB con 5 copias de respaldo
)

# Configuración del logger
logging.basicConfig(
    level=logging.DEBUG,  # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        rotating_handler,          # Guardar en archivo con rotación
        logging.StreamHandler()    # Mostrar logs en consola
    ]
)

# Crear y exportar el logger principal para la aplicación
logger = logging.getLogger("AppLogger")

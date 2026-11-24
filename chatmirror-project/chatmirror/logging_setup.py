import logging
from .config import DATA
def setup():
    logging.basicConfig(filename=DATA/'app.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')

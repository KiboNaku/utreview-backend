
import sys
import threading

from utreview import db
from utreview.routes import *
from utreview.services.automate_backend import automate_backend
from utreview.services.logger import logger


ARG_RUN_ONCE = '--one'

#  initiate backend thread for automation
run_once = ARG_RUN_ONCE in sys.argv

automate_thread = threading.Thread(target=automate_backend, args=[run_once])
automate_thread.daemon = True
if not automate_thread.is_alive():
    automate_thread.start()


if __name__ == '__main__':    
    app.run(debug=True)

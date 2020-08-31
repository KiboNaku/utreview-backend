
import threading

from utreview import app
from utreview.routes import *
from utreview.services.automate_backend import automate_backend


#  command line arguments
ARG_RUN_ONCE = '--once'
run_once = ARG_RUN_ONCE in sys.argv

#  initiate backend thread for automation
automate_thread = threading.Thread(target=automate_backend, args=[run_once])
automate_thread.daemon = True
if not automate_thread.is_alive():
    automate_thread.start()


if __name__ == '__main__':    
    app.run(debug=False)

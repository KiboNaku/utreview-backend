

import threading

from utreview.routes import *
from utreview.services.automate_backend import automate_backend

#  initiate backend thread for automation
automate_thread = threading.Thread(target=automate_backend, args=(1,))
automate_thread.daemon = True
if not automate_thread.is_alive():
    automate_thread.start()

if __name__ == '__main__':    
    app.run(debug=True)

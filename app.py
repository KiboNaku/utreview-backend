

import threading

from utreview import app
from utreview.services.automate_backend import automate_backend

automate_thread = threading.Thread(target=automate_backend, args=(1,))
automate_thread.daemon = True
if not automate_thread.is_alive():
    automate_thread.start()

if __name__ == '__main__':    
    app.run(debug=True)

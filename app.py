

import threading

from utreview import db
from utreview.models.prof import Prof
from utreview.routes import *
from utreview.services.automate_backend import automate_backend
from utreview.services.logger import logger

#  initiate backend thread for automation
# automate_thread = threading.Thread(target=automate_backend, args=(1,))
# automate_thread.daemon = True
# if not automate_thread.is_alive():
#     automate_thread.start()

if __name__ == '__main__':    
    # app.run(debug=True)
    from utreview.services.fetch_prof import parse_prof_csv
    profs = parse_prof_csv('input_data/IRRIS#950_COURSES_OUTPUT.csv')

    cur_profs = Prof.query.all()

    for name, eid in profs:
        if ',' not in name:
            logger.debug(f'Invalid prof name: {name}')
            continue
        
        name = name.lower()
        name = name.split(',')
        last, first = name[0].strip(), name[1].strip()
        last_words = [word.strip() for word in last.split(' ') if len(word.strip()) > 0]
        first_words = [word.strip() for word in first.split(' ') if len(word.strip()) > 0]

        target_prof = None
        for cur_prof in cur_profs:
            found = True

            cur_last, cur_first = cur_prof.last_name.lower(), cur_prof.first_name.lower()
            cur_last_words = [word.strip() for word in cur_last.split(' ') if len(word.strip()) > 0]
            cur_first_words = [word.strip() for word in cur_first.split(' ') if len(word.strip()) > 0]

            for word in cur_last_words:
                if word not in last_words:
                    found = False
                    break
            
            if found:
                for word in cur_first_words:
                    if word not in first_words:
                        found = False
                        break
            
            if found:
                target_prof = cur_prof
                break

        first = first.title()
        last = last.title()

        if target_prof is None:
            logger.debug(f'Adding new prof: {first} {last}')
            new_prof = Prof(first_name=first, last_name=last, eid=eid)
            db.session.add(new_prof)
        else: 
            logger.debug(f'Updaing prof: {target_prof.first_name} {target_prof.last_name} -> {first} {last}')
            target_prof.first_name = first
            target_prof.last_name = last
            target_prof.eid = eid

        db.session.commit()

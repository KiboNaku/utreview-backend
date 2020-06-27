
from utreview import app

if __name__ == '__main__':

    from utreview.services.fetch_ftp import fetch_ftp_files
    fetch_ftp_files('input_data')

    # app.run(debug=True)


from utreview import app

if __name__ == '__main__':

    from utreview.services.fetch_ftp import fetch_ftp_files, parse_ftp
    # fetch_ftp_files('input_data')
    print(parse_ftp('input_data'))

    # app.run(debug=True)

import flask
from flask import request
import tempfile
import io

import main_w as main


class A:
    basic_filter = False
    save_greyscale = False
    radius_div = main.RAD_DIV
    sigma = None
    save_gaussian = False


class App(flask.Flask):
    def __init__(self, name):
        super().__init__(name)

        self.route('/')(self.index)
        self.route('/blurple', methods=['POST', 'GET'])(self.blurple)

    def index(self):
        with open('index.html') as f:
            dat = f.read()

        return dat
    
    def blurple(self):
        if request.method == 'POST':
            if 'file' not in request.files:
                return 'No file selected'
            file_ = request.files['file']
            if file_.filename == '':
                return 'No file selected'
      
            i_file = io.BytesIO()
            i_file.write(file_.read())
            o_file = io.BytesIO()

            main.filter(i_file, file_.filename, o_file, A)

            response = flask.make_response(flask.send_file(o_file, as_attachment=False, attachment_filename=file_.filename))
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers['Cache-Control'] = 'public, max-age=0'
            return response
        return self.index()

        

if __name__ == '__main__':
    App(__name__).run(host='0.0.0.0', port=2053, debug=True, threaded=True)


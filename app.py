from flask import (Flask, flash, request, redirect, url_for, render_template, send_file, send_from_directory)
import os
from werkzeug.utils import secure_filename
from pdf import PDF

UPLOAD_FOLDER = '.\\uploads'
ALLOWED_EXTENSIONS = {'pdf'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '12345'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home(title="Index"):
    return render_template('tools/index.html', title=title)

@app.route("/encrypt", methods=['GET', 'POST'])
def encrypt(title="Encrypt"):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_file_path)
            
            working_file = PDF(full_file_path)
            working_file.encrypt(request.form["Password"])

            download_file_path = app.config['UPLOAD_FOLDER'] + "\\" + ".".join(filename.split(".")[:-1])+"_encrypted.pdf"
            print(download_file_path)
            # send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=".".join(filename.split(".")[:-1])+"_encrypted.pdf")
            return send_file(download_file_path , as_attachment=True)
    return render_template('tools/encrypt.html', title=title)

if __name__ == "__main__":
    app.run(host="127.0.0.1",
            port=5000,
            debug=True)
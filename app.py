import psutil
from typing import Any
from flask import (Flask, flash, request, redirect, url_for, render_template, send_file, session, Response, stream_with_context)
import json
import random
import time
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os
from werkzeug.utils import secure_filename
from pdf import PDF
import random
import threading
import time
import uuid
import glob

UPLOAD_FOLDER = '.\\uploads'
ALLOWED_EXTENSIONS = {'pdf'}
basedir = os.path.abspath(os.path.dirname(__file__))

######################################################################################
# CLASS THREADS
######################################################################################

class EncryptPDF(threading.Thread):
    
    def __init__(self, thread_id, filename, password):
        self.thread_id = thread_id
        self.filename = filename
        self.password = password
        super().__init__()

    def run(self):
        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], self.filename)
        workingfile = PDF(full_file_path)
        self.result = workingfile.encrypt(self.password)

class DecryptPDF(threading.Thread):
    
    def __init__(self, thread_id, filename, password):
        self.thread_id = thread_id
        self.filename = filename
        self.password = password
        super().__init__()

    def run(self):
        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], self.filename)
        workingfile = PDF(full_file_path)
        self.result = workingfile.decrypt(self.password)

class MergePDF(threading.Thread):
    
    def __init__(self, thread_id, files):
        self.thread_id = thread_id
        self.files = files
        super().__init__()

    def run(self):
        workingfile = PDF()
        self.result = workingfile.merge(self.files)        

class SplitPDF(threading.Thread):
    
    def __init__(self, thread_id, files):
        self.thread_id = thread_id
        super().__init__()

    def run(self):
        pass

######################################################################################
# APP FUNCTIONS
######################################################################################

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def print_progress_bar(progress):
  """Prints a progress bar based on the given progress value.

  Args:
    progress: The progress value, between 0 and 100.
  """
  progress = progress
  bar_width = 40
  filled_bars = int(progress * bar_width / 100)
  empty_bars = bar_width - filled_bars
  if progress == 0:
      return ""
  return ("%s%s %d%%" % ("█" * filled_bars, "▒" * empty_bars, progress))

def clear_uploads():
    files = glob.glob(f'{app.config["UPLOAD_FOLDER"]}/*')
    for f in files:
        print(f'Removing file: {f}')
        os.remove(f)

def update_stats(pdf_func):
    stat = Stats(pdf_func=pdf_func)
    db.session.add(stat)
    db.session.commit()

######################################################################################
# APP SETTINGS
######################################################################################

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super secret key'
db = SQLAlchemy(app)

job_dictionary = {}

polling_count = {}
polling_count["Encrypt"] = {"cnt": 0}
polling_count["Decrypt"] = {"cnt": 0}
polling_count["Merge"] = {"cnt": 0}
polling_count["Split"] = {"cnt": 0}
polling_timeout = 1000 #s

######################################################################################
# DATABASE
######################################################################################

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_func = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<pdf_func {self.pdf_func}>'

######################################################################################
# PAGE ROUTES
######################################################################################

@app.route("/")
def home(title="Happy Bread PDF Editor"):
    global job_dictionary, polling_count
    clear_uploads()
    session['uid'] = uuid.uuid4()
    job_dictionary = {}

    return render_template('tools/index.html', title=title)

@app.route("/encrypt", methods=['GET', 'POST'])
def encrypt(title="Encrypt"):
    global job_dictionary
    thread_id = str(session['uid'])
    job_dictionary[title] = {}
    job_dictionary[title][thread_id] = {"progress": 0, "thread_info": None, "status":200}
    if request.method == 'POST':
        job_dictionary[title][thread_id]["progress"] = 0
        print(f'Thread ID: {thread_id}')
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        job_dictionary[title][thread_id]["progress"] = 50
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):   
            filename = f'{thread_id}_{secure_filename(file.filename)}'
            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_file_path)     
            job_dictionary[title][thread_id]["progress"] = 75
            job_dictionary[title][thread_id]["thread_info"] = EncryptPDF(thread_id, filename=filename, password=request.form["Password"])
            job_dictionary[title][thread_id]["thread_info"].start()
            job_dictionary[title][thread_id]["thread_info"].join()
            job_dictionary[title][thread_id]["progress"] = 90
            download_file_path = app.config['UPLOAD_FOLDER'] + "\\" + ".".join(filename.split(".")[:-1])+"_encrypted.pdf"
            job_dictionary[title][thread_id]["progress"] = 99
            time.sleep(1)
            update_stats(pdf_func="Encrypt")
            time.sleep(3)
            job_dictionary[title][thread_id]["status"] = 286
            job_dictionary[title][thread_id]["progress"] = 100
            return send_file(download_file_path , as_attachment=True, download_name=f'encrypted_{filename.replace(thread_id,"")}')
    return render_template('tools/encrypt.html', title=title, thread_id=thread_id)

@app.route("/decrypt", methods=['GET', 'POST'])
def decrypt(title="Decrypt"):
    global job_dictionary
    thread_id = str(session['uid'])
    job_dictionary[title] = {}
    job_dictionary[title][thread_id] = {"progress": 0, "thread_info": None, "status":200}
    if request.method == 'POST':
        job_dictionary[title][thread_id]["progress"] = 0
        print(f'Thread ID: {thread_id}')
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        job_dictionary[title][thread_id]["progress"] = 50
        time.sleep(1)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:   
                filename = f'{thread_id}_{secure_filename(file.filename)}'
                full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(full_file_path)     
                job_dictionary[title][thread_id]["progress"] = 75
                job_dictionary[title][thread_id]["thread_info"] = DecryptPDF(thread_id, filename=filename, password=request.form["Password"])
                job_dictionary[title][thread_id]["thread_info"].start()
                job_dictionary[title][thread_id]["thread_info"].join()
                if isinstance(job_dictionary[title][thread_id]["thread_info"].result, Exception):
                    raise job_dictionary[title][thread_id]["thread_info"].result
                job_dictionary[title][thread_id]["progress"] = 90
                download_file_path = app.config['UPLOAD_FOLDER'] + "\\" + ".".join(filename.split(".")[:-1])+"_decrypted.pdf"
                job_dictionary[title][thread_id]["progress"] = 99
                time.sleep(1)
                update_stats(pdf_func="Decrypt")
                time.sleep(3)
                job_dictionary[title][thread_id]["status"] = 286
                job_dictionary[title][thread_id]["progress"] = 100
                return send_file(download_file_path , as_attachment=True, download_name=f'decrypted_{filename.replace(thread_id,"")}')
            except Exception as e:
                job_dictionary[title][thread_id]["progress"] = 0
                job_dictionary[title][thread_id]["status"] = 286
                flash(f'Something went wrong: {e}')
                return redirect(request.url)
    return render_template('tools/decrypt.html', title=title, thread_id=thread_id)

@app.route("/merge", methods=['GET', 'POST'])
def merge(title="Merge"):
    global job_dictionary
    thread_id = str(session['uid'])
    job_dictionary[title] = {}
    job_dictionary[title][thread_id] = {"progress": 0, "thread_info": None, "status":200}
    if request.method == 'POST':
        job_dictionary[title][thread_id]["progress"] = 0
        print(f'Thread ID: {thread_id}')
        job_dictionary[title][thread_id]["progress"] = 50
        time.sleep(1)
        # Get the list of files from webpage
        files = request.files.getlist("file")
        files_filepath_list = []
        # Iterate for each file in the files List, and Save them
        for file in files:
            filename = f'{thread_id}_{secure_filename(file.filename)}'
            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            files_filepath_list.append(full_file_path)
            job_dictionary[title][thread_id]["progress"] = job_dictionary[title][thread_id]["progress"] + (40/len(files))
            file.save(full_file_path)
        job_dictionary[title][thread_id]["thread_info"] = MergePDF(thread_id, files=files_filepath_list)
        job_dictionary[title][thread_id]["thread_info"].start()
        job_dictionary[title][thread_id]["thread_info"].join()
        job_dictionary[title][thread_id]["progress"] = 99
        time.sleep(1)
        update_stats(pdf_func="Merge")
        time.sleep(3)
        job_dictionary[title][thread_id]["status"] = 286
        job_dictionary[title][thread_id]["progress"] = 100
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "merged.pdf") , as_attachment=True, download_name="merged.pdf")
    return render_template('tools/merge.html', title=title, thread_id=thread_id)

@app.route("/performance", methods=['GET'])
def performance(title="Performance"):
    thread_id = str(session['uid'])
    return render_template('tools/performance.html', title=title, thread_id=thread_id)

@app.route("/split", methods=['GET', 'POST'])
def split(title="Split"):
    global job_dictionary
    thread_id = str(session['uid'])
    job_dictionary[title] = {}
    job_dictionary[title][thread_id] = {"progress": 0, "thread_info": None, "status":200}

    return render_template('tools/split.html', title=title, thread_id=thread_id)

@app.route("/getprogress/<string:title>/<string:id>")
def getprogress(id, title):
    global job_dictionary, polling_count, polling_timeout
    progress = int(job_dictionary.get(title, {}).get(id, {}).get("progress", 0))
    status = job_dictionary.get(title, {}).get(id, {}).get("status", 201)
    if polling_count[title]["cnt"] > polling_timeout:
        polling_count[title]["cnt"] = 0
        return Response("<h2 style='color:red'> OOPSIE! Session Expired. Please Refresh <h2>", status=286, mimetype='application/text')
    polling_count[title]["cnt"] += 1
    return Response(print_progress_bar(progress), status=status, mimetype='application/text')

# ...

@app.route('/getstats_merge')
def getstats_merge():
    merge_cnt = len(Stats.query.filter_by(pdf_func="Merge").all())
    return f'{merge_cnt:,}'

@app.route('/getstats_encrypt')
def getstats_encrypt():
    encrypt_cnt = len(Stats.query.filter_by(pdf_func="Encrypt").all())
    return f'{encrypt_cnt:,}'

@app.route('/getstats_decrypt')
def getstats_decrypt():
    decrypt = len(Stats.query.filter_by(pdf_func="Decrypt").all())
    return f'{decrypt:,}'

@app.route('/chart-data')
def chart_data():
    def generate_random_data():
        while True:
            json_data = json.dumps(
                {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': psutil.cpu_percent(interval=1)})
            yield f"data:{json_data}\n\n"
            time.sleep(1)

    response = Response(stream_with_context(generate_random_data()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@app.route('/network-sent')
def network_sent():
    bytes_sent_MB_1 = psutil.net_io_counters()[0]/1000
    time.sleep(1)
    bytes_sent_MB_2 = psutil.net_io_counters()[0]/1000
    return str(round(bytes_sent_MB_2-bytes_sent_MB_1, 2)) + " kB/s"

@app.route('/network-received')
def network_received():
    bytes_received_MB_1 = psutil.net_io_counters()[1]/1000
    time.sleep(1)
    bytes_received_MB_2 = psutil.net_io_counters()[1]/1000
    return str(round(bytes_received_MB_2-bytes_received_MB_1, 2)) + " kB/s"

@app.errorhandler(404)
def page_not_found(title="404"):
    # note that we set the 404 status explicitly
    return render_template('404.html', title=title), 404

@app.errorhandler(500)
def page_not_found(title="500"):
    return render_template('500.html', title=title), 500

######################################################################################
# MAIN
######################################################################################

if __name__ == "__main__":
    # flask --app app run
    app.run(host="127.0.0.1",
            port=5000,
            debug=True)
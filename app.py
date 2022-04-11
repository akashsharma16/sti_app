from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, render_template, redirect, url_for

from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length

import sys
import logging
import librosa
import scipy
from scipy.signal import butter, lfilter, freqz 
from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np
import acoustics.signal

def ti_calc(x,z,centreFreq,fs):
      
  xoct = acoustics.signal.octavepass(x, centreFreq, fs, 1, order=8, zero_phase=True)
  zoct = acoustics.signal.octavepass(z, centreFreq, fs, 1, order=8, zero_phase=True)

  dt = 0.0001
  #t = np.arange(0, 30, dt)
  #se1 = np.random.randn(len(t))
      
  #s1 = 1.5 * np.sin(2 * np.pi * 10 * t) + nse1 + np.cos(np.pi * t)
      
#   plt.psd(z**2, 512, 1./0.0001, color ="blue")
#   plt.xlabel('Frequency')
#   plt.ylabel('PSD(db)')

#   plt.psd(zoct**2, 512, 1./0.0001, color ="green")
#   plt.xlabel('Frequency')
#   plt.ylabel('PSD(db)')
    
#   plt.suptitle('matplotlib.pyplot.psd() function \
#   Example', fontweight ="bold")
    
#   plt.show()

  xsq = xoct**2
  zsq = zoct**2 

  order = 8
  # fs = 8000       # sample rate, Hz
  cutoff = 50
  # b, a = butter_lowpass(cutoff, fs, order)
  # zlp = butter_lowpass_filter(zsq, cutoff, fs, order)
  zlp = zsq

#   plt.psd(zsq, 512, 1./0.0001, color ="green")
#   plt.xlabel('Frequency')
#   plt.ylabel('PSD(db)')
    
#   plt.psd(zlp, 512, 1./0.0001, color ="red")
#   plt.xlabel('Frequency')
#   plt.ylabel('PSD(db)')

#   plt.suptitle('matplotlib.pyplot.psd() function \
#   Example', fontweight ="bold")
#   plt.show()

  # plt.plot(zlp)
  # plt.show()
  xnorm = librosa.util.normalize(xsq)
  znorm = librosa.util.normalize(zlp)
#   plt.plot(znorm)
#   plt.show()

  winlen = 64
  # winlen = 512
  xfft = librosa.stft(xnorm,n_fft = winlen,hop_length = winlen//8,win_length=winlen,window = 'hann')
  zfft = librosa.stft(znorm,n_fft = winlen,hop_length = winlen//8,win_length=winlen,window = 'hann')

#   zfft.shape

#   plt.psd(zfft, 512, 1./0.0001, color ="blue")
#   plt.xlabel('Frequency')
#   plt.ylabel('PSD(db)')
#   plt.show()

  rxy = scipy.signal.csd(xfft,zfft)
  rxx = scipy.signal.csd(xfft,xfft)
  
  rx = np.real(xfft)
  rz = np.real(zfft)

  mtf = np.divide(rx,rz)
  mtf.shape
  print(mtf)

  uMTF = mtf.mean(axis=0) 
  uMTF.shape
  # uMTF = librosa.util.normalize(uMTF)
  uMTF = np.where(uMTF<=0,0,uMTF)
  uMTF = np.where(uMTF>=0.99,0.99,uMTF)
  print(uMTF)

  unMTF = 1 - uMTF
  unMTF.shape
  print(unMTF)

  from math import log10
  rMTF = np.divide(uMTF,unMTF)
  rMTF = np.divide(uMTF, unMTF, out=np.zeros_like(uMTF), where=unMTF!=0)
#   rMTF.shape

  from numpy.lib.type_check import nan_to_num
  nan_to_num(rMTF)
  rMTF = np.where(rMTF<=0, 1, rMTF)
  # rMTF = np.where(isinf(rMTF), 0, rMTF)
  rMTF

  snr = 10*np.log10(rMTF)
  print(snr)
#   plt.plot(snr)
#   plt.show()

  snr = 10*np.log10(rMTF)
  snr = np.where(snr<=-15, -15, snr)
  snr = np.where(snr>=15, 15, snr)
  snr = snr+15
  # plt.plot(snr)
  snr = np.divide(snr,30)
#   plt.plot(snr)
#   plt.show()
  
  ti = sum(snr)/len(snr)

  return ti

def sti_calc(x,z,fs):
    wt = [1, 1, 1, 1, 0.75, 0.425]
    sum(wt)

    freq = [125, 250, 500, 1000, 2000, 4000]
    ti = []
  
    for centfreq in freq:
        print("CALCULATING FOR CENTRE FREQUENCY = ", centfreq)
        ti.append(ti_calc(x,z,centfreq,fs))
    
    sti = ti[0]*wt[0] + ti[1]*wt[1] + ti[2]*wt[2] + ti[3]*wt[3] + ti[4]*wt[4] + ti[5]*wt[5]
    sti = sti/sum(wt)
    return sti

app = Flask(__name__)



@app.route("/")
def start():
    return render_template('home.html')

@app.route('/upload', methods=['GET','POST'])
def upload_file():
    # check if post request has the file part
    app.logger.info('start')
    if 'cleanSignal' not in request.files:
        err_msg = 'No file part!'
        return render_template('upload.html'), 405
    app.logger.info('clean')
    if 'degradedSignal' not in request.files:
        err_msg = 'No file part!'
        return render_template('upload.html'), 405
    app.logger.info('degrad')
    cfile = request.files['cleanSignal']
    dfile = request.files['degradedSignal']
    if cfile.filename == '':
        return render_template('upload.html'), 405
    if dfile.filename == '':
        return render_template('upload.html'), 405
    # print('Hello world!', file=sys.stderr)
    return 'Successfully Uploaded'

    # # check if filename is empty (no file selected)
    # if file.filename == '':
    #     err_msg = 'No file selected!'
    #     return err_msg, 400

    # # if file extension is correct, analyze audio
    # if check_ext(file.filename):
    #     dbfs, t_rms, fs = analyze_wav(file)
    #     return jsonify(rms=dbfs, t_rms=t_rms, fs=fs, framesize=DEFAULT_FRAMESIZE)
    # else:
    #     err_msg = ('Wrong file extension! Allowed: ' +
    #                ', '.join(ALLOWED_EXTENSIONS))
    #     return err_msg, 415


if __name__ == "__main__":
    app.run(debug=True)

# @app.route('/home')
# def home():
#     return render_template('home.html')

# @app.route('/', methods=['POST', 'GET'])
# @login_required
# def index():
#     if request.method == 'POST':
#         task_content =request.form['content']
#         task_status = request.form['status']
#         new_task = Todo(content=task_content,status=task_status,uniq_id=current_user.id)

#         try:
#             db.session.add(new_task)
#             db.session.commit()
#             return redirect('/')
#         except:
#             return 'There was an issue adding your task'

#     else:
#         tasks = Todo.query.filter_by(uniq_id=current_user.id).all()
#         return render_template('index.html', tasks=tasks)


# @app.route('/delete/<int:id>')
# @login_required
# def delete(id):
#     task_to_delete = Todo.query.get_or_404(id)
#     db.session.delete(task_to_delete)
#     db.session.commit()
#     return redirect('/')

# @app.route('/update/<int:id>', methods=['GET', 'POST'])
# @login_required
# def update(id):
#     task = Todo.query.get_or_404(id)

#     if request.method == 'POST':
#         task.status = request.form['status']
#         db.session.commit()
#         return redirect('/')

#     else:
#         return render_template('update.html', task=task)


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('index'))

# if __name__ == "__main__":
#     app.run(debug=True)
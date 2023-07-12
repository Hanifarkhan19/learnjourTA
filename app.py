from flask import Flask, render_template, request, redirect, make_response,url_for, flash,session, abort
import speech_recognition as sr
from pydub import AudioSegment
import datetime
from werkzeug.utils import secure_filename
import math
import io
import os
import re
from flask_mysqldb import MySQL, MySQLdb
from slugify import slugify

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/uploads/images'

app.secret_key = "Warsistant"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'warsistant'
app.config['MYSQL_CUSRSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


        
@app.route('/')
@app.route('/home')
def index():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM artikel")
    curl.execute("SELECT * FROM testimoni")
    testimoni = curl.fetchall()
    blog = cur.fetchall()
    cur.close()
    return render_template('user/home.html',blog=blog, testimoni=testimoni) 
   
@app.route('/dashboard')
def dashboard():
    if 'islogin' in session:
        return render_template('dashboard/index.html') 
    else:
        return redirect(url_for('login'))
    

@app.route('/pesan')
def pesan():
    if 'islogin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM message")
        pesan = cur.fetchall()
        cur.close()
        return render_template('dashboard/pesan.html',pesan=pesan)  
    else:
        return redirect(url_for('login'))
    

@app.route('/testimoni')
def testimoni():
    if 'islogin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM testimoni")
        testimoni = cur.fetchall()
        cur.close()
        return render_template('dashboard/testimoni.html',testimoni=testimoni)
    else:
        return redirect(url_for('login'))
    
@app.route('/register')
def register():
    if 'islogin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()
        return render_template('dashboard/register.html',users=users)
    else:
        return redirect(url_for('login'))
     
@app.route('/edit-artikel/<string:id_artikel>')
def editArtikel(id_artikel):
    if 'islogin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM artikel where id_artikel = %s",(id_artikel,))
        artikel = cur.fetchone()
        cur.close()
        flash("Berhasil, Artikel Telah Di Update")
        print(artikel)
        return render_template('dashboard/editArtikel.html',artikel=artikel)
    else:
        return redirect(url_for('login'))
     
   
@app.route('/artikel')
def artikel():
    if 'islogin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM artikel")
        result = cur.fetchall()
        cur.close()
        return render_template('dashboard/artikel.html',result=result)
    else:
        return redirect(url_for('login'))
     

@app.route('/<string:id_artikel>/<string:judul>')
def detail(id_artikel,judul):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM artikel where id_artikel = %s",(id_artikel,))
    result = cur.fetchone()
    cur.close()
    return render_template('user/detail.html',result=result) 
   
@app.route('/formartikel')
def formArtikel():
    if 'islogin' in session:
        return render_template('dashboard/formArtikel.html')
    else:
        return redirect(url_for('login'))
       
        
@app.route("/upload", methods=["GET", "POST"])
def upload():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM artikel")
    curl.execute("SELECT * FROM testimoni")
    testimoni = curl.fetchall()
    blog = cur.fetchall()
    cur.close()
    transcript = ""
    duration_str = ''
    i = ''
    segment_info = []
    if request.method == "POST":
        print("FORM DATA RECEIVED")
    
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        # Memeriksa ekstensi file
        allowed_extensions = ["wav"]
        if file.filename.split(".")[-1].lower() not in allowed_extensions:
            return "Hanya file dengan ekstensi WAV yang diizinkan."

        if file:
            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                data = recognizer.record(source)
                segment_length = 60 * 1000  # dalam milidetik
                audio = AudioSegment.from_wav(file)
                segment_count = math.ceil(audio.duration_seconds * 1000 / segment_length)
                print(segment_count)
                
                for i in range(segment_count):
                    segment_start = i * segment_length
                    segment_end = min(audio.duration_seconds * 1000, (i + 1) * segment_length)
                    segment_file_name = f"segment_{i+1}.wav"
                    segment = audio[segment_start:segment_end]
                    segment.export(segment_file_name, format="wav")
                    print(f"Segmen {i*10}: {segment_file_name}")
                
                    with sr.AudioFile(segment_file_name) as source:
                        segment_audio = recognizer.record(source)
                        transcript = recognizer.recognize_google(segment_audio, language="id-ID")
                        duration_start = segment_start / 1000
                        duration_selesai = segment_end / 1000
                        duration_str = str(datetime.timedelta(seconds=duration_start)).split('.')[0]
                        duration_end = str(datetime.timedelta(seconds=duration_selesai)).split('.')[0]
                    
                       
                        print(f"Transkripsi segmen {i+1}: ({i*10}) : {transcript}")
                        
                        segment_info.append((i*10, segment_file_name, transcript, duration_str, duration_end))
                        
        
    return render_template('user/home.html', transcript=transcript, i=i, segment_info=segment_info , blog=blog,testimoni=testimoni)


@app.route('/download_transcript', methods=['POST'])
def download_transcript():
    transcript = request.form.get('content')
    if not transcript:
        abort(400)

    transcript = re.sub('<div>|</div>|&nbsp;', '', transcript)
    # Create a text file containing the transcript
    text_file = io.StringIO()
    text_file.write(transcript)

    # Generate the response with the text file as content
    response = make_response(text_file.getvalue())
    response.headers.set('Content-Disposition', 'attachment', filename='transcript.txt')
    response.headers.set('Content-Type', 'text/plain')
    return response

@app.route('/add-artikel', methods=["POST"])
def storeArtikel():
    cur = mysql.connection.cursor()
    judul = request.form['judul']
    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)
    tanggal = request.form["tanggal"]
    status = request.form['status']
    artikel = request.form['artikel']
    slug = slugify(artikel)
    cur.execute("INSERT INTO artikel (judul,image,tanggal,status,artikel,slug) VALUES (%s,%s,%s,%s,%s,%s)",(judul,filename,tanggal,status,artikel,slug))
    mysql.connection.commit()
    cur.close()
    flash("Berhasil, Artikel Telah Ditambah")
    return redirect(url_for('artikel'))

@app.route('/add-message', methods=["POST"])
def addMessage():
    cur = mysql.connection.cursor()
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']
    cur.execute("INSERT INTO message (name,email,subject,message) VALUES (%s,%s,%s,%s)",(name,email,subject,message))
    mysql.connection.commit()
    cur.close()
    flash('Pesan Berhasil dikirim')
    return redirect(url_for('index'))

@app.route('/add-testimoni', methods=["POST"])
def addTestimoni():
    cur = mysql.connection.cursor()
    nama= request.form['nama']
    jobdesk = request.form['jobdesk']
    testimoni = request.form['testimoni']
    testi = re.sub('<div>|</div>|&nbsp;', '', testimoni)
    cur.execute("INSERT INTO testimoni (nama,jobdesk,testimoni) VALUES (%s,%s,%s)",(nama,jobdesk,testi))
    mysql.connection.commit()
    cur.close()
    flash('Testimoni Bershasil ditambahkan')
    return redirect(url_for('testimoni'))

# AUTENTIKASI AKUN
@app.route('/login', methods =['GET', 'POST'])
def login():
    if 'islogin' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form:
            name = request.form['name']
            password = request.form['password']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE name = % s AND password = % s', (name, password, ))
            account = cursor.fetchone()
            if account:
                session['islogin'] = True
                session['id_users'] = account['id_users']
                session['name'] = account['name']
                return redirect(url_for('dashboard'))
            else:
                flash("Gagal, User Tidak Ditemukan")
                return redirect(url_for('login'))
    else: 
         return render_template('dashboard/login.html')

@app.route('/add-akun', methods=["POST"])
def storeAkun():
    cur = mysql.connection.cursor()  
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",(name,email,password))
    mysql.connection.commit()
    cur.close()
    flash("Berhasil, User Telah Ditambahkan")
    return redirect(url_for('register'))

@app.route('/artikel-edit/<string:id_artikel>', methods=["POST"])
def artikelEdit(id_artikel):
    cur = mysql.connection.cursor()  
    judul = request.form['judul']
    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)
    tanggal = request.form["tanggal"]
    status = request.form['status']
    artikel = request.form['artikel']
    slug = slugify(artikel)
    cur.execute("UPDATE artikel SET judul=%s, image=%s, tanggal=%s, status=%s, artikel=%s, slug=%s WHERE id_artikel=%s", (judul, filename, tanggal, status, artikel, slug, id_artikel,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('artikel'))

@app.route('/hapus-artikel/<string:id_artikel>', methods=['POST', 'GET'])
def hapus_data(id_artikel):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM artikel WHERE id_artikel=%s", (id_artikel,))
    mysql.connection.commit()
    cursor.close()
    flash("Artikel Telah Di hapus")
    return redirect(url_for('artikel'))


@app.route('/logout')
def logout():
    session.pop('islogin',None)
    session.pop('id_users',None)
    session.pop('name',None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, threaded=True)

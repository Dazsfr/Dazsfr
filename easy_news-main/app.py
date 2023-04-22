import string 
import random
import sqlite3
import pytz
import datetime
import os
from flask import *

app = Flask(__name__)

app.secret_key = b"SADBKHWGDIEWCIBECIUBEIUBIEF"

@app.route("/test")
def index():
	return render_template("index.html")

@app.route("/static/<file>")
def send_static_file(file):
	try:
		return send_file("static/"+file)
	except:
		return ""

@app.route("/panel")
def panel_handler():
	otp = request.cookies.get("otp")
	if otp:
		return "1"
	else:
		return redirect("/login")

@app.route("/login",methods=["POST","GET"])
def login_page():
	if (request.method == "GET"):
		return render_template("login.html")
	else:
		return ""

@app.route("/sso/<code>")
def sso_login(code):
	status = check_sso(code)
	if (status == "true"):
		resp = make_response(redirect("/manage"))
		creds = code
		resp.set_cookie('sso-auth', creds)
		return resp
	else:
		return "Неверный код доступа, пожалуйста, обратитесь к администратору за сбросом."

@app.route("/logout")
def logout_endpoint():
	resp = make_response(redirect("/"))
	resp.set_cookie('sso-auth', '', expires=0)
	return resp

@app.route("/upd_line",methods=["POST"])
def change_line():
	token = request.cookies.get("sso-auth")
	if (token):
		status = check_sso(token)
		if (status == "true"):
			new_msg = request.form.get("new_msg")
			set_new_line(new_msg)
			return redirect("/manage")
		else:
			return redirect("/logout")
	else:
		return redirect("/")

@app.route("/upload",methods=["POST","GET"])
def upload_new():
	token = request.cookies.get("sso-auth")
	if (token):
		status = check_sso(token)
		if (status == "true"):
			if (request.method == "GET"):
				un = sso_get_un(token)
				return render_template("upload.html",name=un)
			else:
				if 'file' not in request.files:
					print('No file part')
					return redirect(request.url)
				file = request.files['file']
				if file.filename == '':
					print('No selected file')
					return redirect(request.url)
				new_id = request.form.get("nw_name")
				filename = new_id
				file.save(os.path.join("static", filename))
				currentime = str(datetime.datetime.now())
				dbadd_nw(new_id,"/static/"+new_id,currentime)
				return redirect("/manage")
		else:
			return redirect("/logout")
	else:
		return redirect("/")

@app.route("/manage")
def board_manager():
	token = request.cookies.get("sso-auth")
	if (token):
		status = check_sso(token)
		if (status == "true"):
			un = sso_get_un(token)
			news = get_raw_news()
			line_ = get_text()
			return render_template("lk.html",name=un,split=split_,nl=news,line=line_)
		else:
			return redirect("/logout")
	else:
		return redirect("/")

@app.route("/delete/<id>")
def delete_news(id):
	token = request.cookies.get("sso-auth")
	if (token):
		status = check_sso(token)
		if (status == "true"):
			os.remove("static/"+id)
			dbdelete_nw(id)
			return redirect("/manage")
		else:
			return redirect("/logout")
	else:
		return redirect("/")

@app.route("/")
def index_test():
	return render_template("test_slider.html")

@app.route("/get_liveline")
def liveline():
	kys = get_text()
	return kys

@app.route("/get_news")
def newsgetter():
	news = get_news_list()
	return str(news)

@app.route("/get_time")
def livetime():
	currentime = datetime.datetime.now()
	time = currentime.strftime("%H:%M")
	return time

def generate():
	one = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
	two = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
	three = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
	four = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
	five = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
	random_token = one+"-"+two+"-"+three+"-"+four+"-"+five
	return random_token

def dbadd_nw(nw_name,nw_link,nw_date):
	con = sqlite3.connect("news_db.db")
	cur = con.cursor()
	cur.execute("INSERT INTO sch_changes (date,img,custom_id) VALUES (?,?,?)",(nw_date,nw_link,nw_name) )
	con.commit()
	con.close()

def dbdelete_nw(id):
	con = sqlite3.connect("news_db.db")
	cur = con.cursor()
	cur.execute("DELETE FROM sch_changes WHERE custom_id == '"+id+"'")
	con.commit()
	con.close()


def set_new_line(new_text):
	con = sqlite3.connect('news_db.db')
	cur = con.cursor()
	cur.execute("UPDATE news_line SET text = '"+new_text+"' WHERE id == 'BASIC_NEWS'")
	con.commit()
	con.close()

def get_text():
	con = sqlite3.connect('news_db.db')
	cur = con.cursor()
	cur.execute("SELECT text FROM news_line WHERE id = 'BASIC_NEWS'")
	resp = cur.fetchone()
	con.close()
	return resp[0]

def get_raw_news():
	con = sqlite3.connect('news_db.db')
	cur = con.cursor()
	cur.execute("SELECT * FROM sch_changes")
	resp = cur.fetchall()
	con.close()
	return resp

def get_news_list():
	con = sqlite3.connect('news_db.db')
	cur = con.cursor()
	cur.execute("SELECT img FROM sch_changes")
	resp = cur.fetchall()
	con.close()
	try:
		print(resp)
		last = ""
		for image_file in resp:
			last += image_file[0] + ','
		return last[:-1]
	except:
		return []

def sso_get_un(code):
	con = sqlite3.connect('news_db.db')
	cur = con.cursor()
	cur.execute("SELECT username FROM sso_keys WHERE key = '"+str(code)+"'")
	resp = cur.fetchall()
	con.close()
	try:
		if (resp[0][0] != ""):
			return resp[0][0]
		else:
			return None
	except:
		return None

def split_(string_to_split,splitter):
	return string_to_split.split(splitter)

def check_sso(code):
	con = sqlite3.connect('news_db.db')
	cur = con.cursor()
	cur.execute("SELECT username FROM sso_keys WHERE key = '"+str(code)+"'")
	resp = cur.fetchall()
	con.close()
	try:
		if (resp[0][0] != ""):
			return "true"
		else:
			return "false"
	except:
		return "false"


if (__name__ == "__main__"):
	app.run(debug=True)
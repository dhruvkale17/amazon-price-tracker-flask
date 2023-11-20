import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re, requests
import schedule
import threading
from bs4 import BeautifulSoup
import smtplib

app = Flask(__name__)

load_dotenv()

#DB configs--
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
db = SQLAlchemy(app)

#Table in the DB
class PriceTracker(db.Model):
    __tablename__='Data'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    servedStatus = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime,default=datetime.now)
    
    
    def __init__(self,url,budget,email):
        self.url = url
        self.budget = budget
        self.email = email
        
	
    def __repr__(self):
        return '<Entry %r>' % self.id

#creates outlook mailing server
#def create_mail_server():
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
FROM_EMAIL = os.getenv('MAIL_USERNAME')
PASSWORD = os.getenv('MAIL_PASSWORD')
smtp = smtplib.SMTP(HOST,PORT)

status_code, response = smtp.ehlo()
print(f"echoing: {status_code} {response}")

status_code, response = smtp.starttls()
print(f"starting tls: {status_code} {response}")

status_code, response = smtp.login(FROM_EMAIL, PASSWORD)
print(f"logging in: {status_code} {response}")

#Sends mail	
def send_email(url,email):
	TO_EMAIL=email
	message = f"""Subject:Price has reduced, shop now!

	Price has dropped for this item you are looking for. Product link: {url}

	Regards,
	AmazonPriceTracker
	"""
	smtp.sendmail(FROM_EMAIL,TO_EMAIL,message)

#header for get-request
headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}

#checks if price< | price> budget
def check_price(url,budget):
	page = requests.get(url, headers=headers, timeout=5)
	soup = BeautifulSoup(page.content, 'html.parser')
	try:
		price = soup.find('span', {'class':'a-price-whole'}).get_text()
		price = int(re.sub(r'\D', '', price))
		if(price <= budget):
			return True
		else:
			return False
	except:
		return "None"

#Multithreads and schedules it
def bgthread():
	print("Thread started")
	with app.app_context():
		schedule.every(10).minutes.do(task)
		while True:
			schedule.run_pending()

def task():
	print("task started")
	unserved = PriceTracker.query.filter_by(servedStatus=False).all()
	for u in unserved:	
		print(u.id)
		status = check_price(u.url, u.budget)
		print(status)
		if status is True:
			u.servedStatus = True
			#send_email(u.url, u.email)
			print("sent mail")

		if status is None:
			print("Can't fetch price! error!")

	db.session.commit()

#flask view here--
#Adds new entries
@app.route('/', methods=['GET','POST'])
def index():
	if request.method == 'POST':
		url = request.form['url']
		budget = request.form['budget']
		email = request.form['email']
		print(url)
		entry = PriceTracker(url,int(budget),email)
		try:
			db.session.add(entry)
			db.session.commit()
			print("done")
		except:
			return 'Error adding new entry'
		
		return redirect('/')
	return render_template('index.html')

# main driver function
if __name__ == '__main__':

	t1 = threading.Thread(target=bgthread)
	t1.start()
	
	app.run(debug=True)

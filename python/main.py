from flask import Flask, request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)

SPREADSHEET_ID = '1yazHtr3Ye8ye489mHb-Oasbc_PI-0qp2qAvlqvnxhso'
RANGE_NAME = 'Sheet1!A1'
SERVICE_ACCOUNT_FILE = './google_sheet_credentials.json'

@app.route('/')
def index():
	return 'Google Sheets logging app is live.'

@app.route('/submit', methods=['GET'])
def submit():
	# Student information
	student_first = request.args.get('studentFirstName')
	student_last = request.args.get('studentLastName')
	student_email = request.args.get('studentEmail')
	student_phone = request.args.get('studentPhone')
	student_age = request.args.get('studentAge')
	student_school = request.args.get('studentSchool')
	
	# Parent/Guardian 1 information
	parent1_first = request.args.get('parent1FirstName')
	parent1_last = request.args.get('parent1LastName')
	parent1_email = request.args.get('parent1Email')
	parent1_phone = request.args.get('parent1Phone')
	
	# Parent/Guardian 2 information (optional)
	parent2_first = request.args.get('parent2FirstName', '')
	parent2_last = request.args.get('parent2LastName', '')
	parent2_email = request.args.get('parent2Email', '')
	parent2_phone = request.args.get('parent2Phone', '')

	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	creds = service_account.Credentials.from_service_account_file(
		SERVICE_ACCOUNT_FILE,
		scopes=["https://www.googleapis.com/auth/spreadsheets"]
	)
	service = build('sheets', 'v4', credentials=creds)
	sheet = service.spreadsheets()

	values = [[timestamp, student_first, student_last, student_email, student_phone, 
	           student_age, student_school, parent1_first, parent1_last, parent1_email, 
	           parent1_phone, parent2_first, parent2_last, parent2_email, parent2_phone]]

	body = {'values': values}
	sheet.values().append(
		spreadsheetId=SPREADSHEET_ID,
		range=RANGE_NAME,
		valueInputOption='RAW',
		insertDataOption='INSERT_ROWS',
		body=body
	).execute()

	return 'Data saved successfully.'

from flask import Flask, request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)

SPREADSHEET_ID = '1yazHtr3Ye8ye489mHb-Oasbc_PI-0qp2qAvlqvnxhso'
RANGE_NAME = 'Sheet1!A1'
SERVICE_ACCOUNT_FILE = './google_sheet_credentials.json.json'

@app.route('/')
def index():
	return 'Google Sheets logging app is live.'

@app.route('/submit', methods=['GET'])
def submit():
	parent_first = request.args.get('parent_first')
	parent_last = request.args.get('parent_last')
	student_first = request.args.get('student_first')
	student_last = request.args.get('student_last')
	parent_email = request.args.get('parent_email')
	parent_phone = request.args.get('parent_phone')
	student_email = request.args.get('student_email')
	student_phone = request.args.get('student_phone')

	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

	creds = service_account.Credentials.from_service_account_file(
		SERVICE_ACCOUNT_FILE,
		scopes=["https://www.googleapis.com/auth/spreadsheets"]
	)
	service = build('sheets', 'v4', credentials=creds)
	sheet = service.spreadsheets()

	values = [[timestamp, parent_first, parent_last, student_first, student_last,
	           parent_email, parent_phone, student_email, student_phone]]

	body = {'values': values}
	sheet.values().append(
		spreadsheetId=SPREADSHEET_ID,
		range=RANGE_NAME,
		valueInputOption='RAW',
		insertDataOption='INSERT_ROWS',
		body=body
	).execute()

	return 'Data saved successfully.'

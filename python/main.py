from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
import logging

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SPREADSHEET_ID = '1yazHtr3Ye8ye489mHb-Oasbc_PI-0qp2qAvlqvnxhso'
RANGE_NAME = 'Sheet1!A1'
SERVICE_ACCOUNT_FILE = './google_sheet_credentials.json'

@app.route('/')
def index():
	return 'Google Sheets logging app is live.'

@app.route('/submit', methods=['GET', 'OPTIONS'])
def submit():
	# Handle preflight OPTIONS request
	if request.method == 'OPTIONS':
		response = app.make_default_options_response()
		headers = response.headers
		headers['Access-Control-Allow-Origin'] = '*'
		headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
		headers['Access-Control-Allow-Headers'] = 'Content-Type'
		return response
	
	# Student information
	student_first = request.args.get('studentFirstName', '')
	student_last = request.args.get('studentLastName', '')
	student_email = request.args.get('studentEmail', '')
	student_phone = request.args.get('studentPhone', '')
	student_age = request.args.get('studentAge', '')
	student_school = request.args.get('studentSchool', '')
	
	# Parent/Guardian 1 information
	parent1_first = request.args.get('parent1FirstName', '')
	parent1_last = request.args.get('parent1LastName', '')
	parent1_email = request.args.get('parent1Email', '')
	parent1_phone = request.args.get('parent1Phone', '')
	
	# Parent/Guardian 2 information (optional)
	parent2_first = request.args.get('parent2FirstName', '')
	parent2_last = request.args.get('parent2LastName', '')
	parent2_email = request.args.get('parent2Email', '')
	parent2_phone = request.args.get('parent2Phone', '')

	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	
	# Log the submission attempt
	logger.info(f"Student submission: {student_first} {student_last} at {timestamp}")

	# Check if credentials file exists
	if not os.path.exists(SERVICE_ACCOUNT_FILE):
		logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
		# Save to backup file since Google Sheets isn't available
		try:
			backup_data = {
				'timestamp': timestamp,
				'student_first': student_first,
				'student_last': student_last,
				'student_email': student_email,
				'student_phone': student_phone,
				'student_age': student_age,
				'student_school': student_school,
				'parent1_first': parent1_first,
				'parent1_last': parent1_last,
				'parent1_email': parent1_email,
				'parent1_phone': parent1_phone,
				'parent2_first': parent2_first,
				'parent2_last': parent2_last,
				'parent2_email': parent2_email,
				'parent2_phone': parent2_phone
			}
			
			with open('student_submissions_backup.txt', 'a') as f:
				f.write(f"{backup_data}\n")
			
			logger.info(f"Saved backup data for {student_first} {student_last} (no credentials)")
			return jsonify({
				'status': 'success',
				'message': 'Data saved to backup. We will process it manually.',
				'timestamp': timestamp
			})
		except Exception as backup_error:
			logger.error(f"Backup save failed: {str(backup_error)}")
			return jsonify({
				'status': 'error',
				'message': 'Server configuration error. Please contact support.'
			}), 500

	try:
		# Try to connect to Google Sheets
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
		result = sheet.values().append(
			spreadsheetId=SPREADSHEET_ID,
			range=RANGE_NAME,
			valueInputOption='RAW',
			insertDataOption='INSERT_ROWS',
			body=body
		).execute()
		
		logger.info(f"Successfully saved data for {student_first} {student_last}")
		return jsonify({
			'status': 'success',
			'message': 'Data saved successfully.',
			'timestamp': timestamp
		})

	except Exception as e:
		logger.error(f"Error saving student data: {str(e)}")
		
		# Try to save to a local backup file if Google Sheets fails
		try:
			backup_data = {
				'timestamp': timestamp,
				'student_first': student_first,
				'student_last': student_last,
				'student_email': student_email,
				'student_phone': student_phone,
				'student_age': student_age,
				'student_school': student_school,
				'parent1_first': parent1_first,
				'parent1_last': parent1_last,
				'parent1_email': parent1_email,
				'parent1_phone': parent1_phone,
				'parent2_first': parent2_first,
				'parent2_last': parent2_last,
				'parent2_email': parent2_email,
				'parent2_phone': parent2_phone
			}
			
			# Save to backup file
			with open('student_submissions_backup.txt', 'a') as f:
				f.write(f"{backup_data}\n")
			
			logger.info(f"Saved backup data for {student_first} {student_last}")
			return jsonify({
				'status': 'success',
				'message': 'Data saved to backup. We will process it manually.',
				'timestamp': timestamp
			})
			
		except Exception as backup_error:
			logger.error(f"Backup save failed: {str(backup_error)}")
			return jsonify({
				'status': 'error',
				'message': 'Unable to save data. Please try again later or contact us directly.',
				'error': str(e)
			}), 500

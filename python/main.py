from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
import logging
import warnings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Suppress the oauth2client deprecation warning
warnings.filterwarnings("ignore", message="file_cache is only supported with oauth2client<4.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Also suppress the warning at the googleapiclient level
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = os.getenv('RANGE_NAME', 'Sheet1!A1')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# Validate required environment variables
if not SPREADSHEET_ID:
	raise ValueError("SPREADSHEET_ID environment variable is required")

required_google_env_vars = [
	'GOOGLE_TYPE', 'GOOGLE_PROJECT_ID', 'GOOGLE_PRIVATE_KEY_ID',
	'GOOGLE_PRIVATE_KEY', 'GOOGLE_CLIENT_EMAIL', 'GOOGLE_CLIENT_ID',
	'GOOGLE_AUTH_URI', 'GOOGLE_TOKEN_URI'
]

for var in required_google_env_vars:
	if not os.getenv(var):
		raise ValueError(f"{var} environment variable is required")

# Build credentials dictionary from environment variables
GOOGLE_CREDENTIALS_DICT = {
	'type': os.getenv('GOOGLE_TYPE'),
	'project_id': os.getenv('GOOGLE_PROJECT_ID'),
	'private_key_id': os.getenv('GOOGLE_PRIVATE_KEY_ID'),
	'private_key': os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
	'client_email': os.getenv('GOOGLE_CLIENT_EMAIL'),
	'client_id': os.getenv('GOOGLE_CLIENT_ID'),
	'auth_uri': os.getenv('GOOGLE_AUTH_URI'),
	'token_uri': os.getenv('GOOGLE_TOKEN_URI'),
	'auth_provider_x509_cert_url': os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
	'client_x509_cert_url': os.getenv('GOOGLE_CLIENT_X509_CERT_URL', ''),
	'universe_domain': os.getenv('GOOGLE_UNIVERSE_DOMAIN', 'googleapis.com')
}

@app.route('/')
def index():
	return 'Google Sheets logging app is live.'

@app.route('/test-permissions')
def test_permissions():
	try:
		# Get the directory where main.py is located
		app_dir = os.path.dirname(__file__)
		test_file_path = os.path.join(app_dir, 'test_write_permissions.txt')
		
		# Try to write a test file
		with open(test_file_path, 'w') as f:
			f.write('Test write permissions\n')
			f.flush()
		
		# Try to read it back
		with open(test_file_path, 'r') as f:
			content = f.read()
		
		# Clean up the test file
		os.remove(test_file_path)
		
		return jsonify({
			'status': 'success',
			'message': 'Write permissions OK',
			'directory': app_dir,
			'test_content': content.strip()
		})
		
	except Exception as e:
		return jsonify({
			'status': 'error',
			'message': f'Write permission denied: {str(e)}',
			'directory': os.path.dirname(__file__) if '__file__' in globals() else 'unknown'
		})

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
			backup_line = f"{timestamp}|{student_first}|{student_last}|{student_email}|{student_phone}|{student_age}|{student_school}|{parent1_first}|{parent1_last}|{parent1_email}|{parent1_phone}|{parent2_first}|{parent2_last}|{parent2_email}|{parent2_phone}\n"
			
			backup_file_path = os.path.join(os.path.dirname(__file__), 'student_submissions_backup.txt')
			
			with open(backup_file_path, 'a', encoding='utf-8') as f:
				f.write(backup_line)
				f.flush()  # Force write to disk
			
			logger.info(f"Saved backup data for {student_first} {student_last} (no credentials) to {backup_file_path}")
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
		creds = service_account.Credentials.from_service_account_info(
			GOOGLE_CREDENTIALS_DICT,
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
			backup_line = f"{timestamp}|{student_first}|{student_last}|{student_email}|{student_phone}|{student_age}|{student_school}|{parent1_first}|{parent1_last}|{parent1_email}|{parent1_phone}|{parent2_first}|{parent2_last}|{parent2_email}|{parent2_phone}\n"
			
			# Try to save to backup file in current directory
			backup_file_path = os.path.join(os.path.dirname(__file__), 'student_submissions_backup.txt')
			
			with open(backup_file_path, 'a', encoding='utf-8') as f:
				f.write(backup_line)
				f.flush()  # Force write to disk
			
			logger.info(f"Saved backup data for {student_first} {student_last} to {backup_file_path}")
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

if __name__ == '__main__':
	debug_mode = FLASK_ENV == 'development'
	app.run(host='0.0.0.0', port=FLASK_PORT, debug=debug_mode)

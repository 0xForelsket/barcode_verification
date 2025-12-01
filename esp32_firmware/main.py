from server import HTTPServer
import app_logic

# Initialize
app_logic.load_state()

# Setup Server
server = HTTPServer(port=80)

# Register Routes
@server.route('/api/status')
def status(body):
    return app_logic.get_status(body)

@server.route('/api/job/start', 'POST')
def start(body):
    return app_logic.start_job(body)

@server.route('/api/job/end', 'POST')
def end(body):
    return app_logic.end_job(body)

@server.route('/api/scan', 'POST')
def scan(body):
    return app_logic.scan_barcode(body)

@server.route('/api/hourly_stats')
def hourly(body):
    return app_logic.get_hourly_stats(body)

# Start
print("Starting Barcode Verification System...")
server.start()

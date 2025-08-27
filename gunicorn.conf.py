"""Gunicorn configuration file"""
import multiprocessing
import os

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Time limit in seconds before a worker is killed and restarted
timeout = 60

# Listen on all interfaces
port = os.environ.get('PORT', '8000')
bind = f"0.0.0.0:{port}"

# Log level
loglevel = "info"

# Process name
proc_name = "rozoom_web_app"

# Enable pre-forking
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

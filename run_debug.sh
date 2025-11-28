#!/bin/bash
# Run web app in debug mode with logs
export FLASK_APP=web_app.py
export FLASK_ENV=development
python3 web_app.py

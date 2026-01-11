#!/bin/bash
cd /home/ubuntu/football_app
source venv/bin/activate
python run_pre_match_analysis.py >> /tmp/pre_match_cron.log 2>&1

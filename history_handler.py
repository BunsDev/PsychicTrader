import json
import time
from datetime import datetime

import os


class HistoryHandler:

    def __init__(self, history_dir='./history'):
        self.history_dir = history_dir
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def save_session_data(self, session_data):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"{self.history_dir}/{timestamp}.txt", 'w') as file:
            json.dump(session_data, file)

    def get_session_data(self, timestamp):
        with open(f"{self.history_dir}/{timestamp}.txt", 'r') as file:
            return json.load(file)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import threading
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "api_keys": {
                    "rugcheck": "",
                    "tweetscout": "",
                    "gmgn": "",
                    "bullx": ""
                },
                "blacklists": {
                    "tokens": [],
                    "developers": []
                },
                "thresholds": {
                    "risk_score": 70,
                    "volume_spike": 3.0,
                    "social_sentiment": 0.5
                }
            }
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

class APIClient:
    def __init__(self, config):
        self.config = config
        self.endpoints = {
            "rugcheck": "https://api.rugcheck.xyz/v1/analyze",
            "tweetscout": "https://api.tweetscout.io/v3/sentiment",
            "gmgn": "https://api.gmgn.ai/chain/v1/eth/score",
            "bullx": "https://api.bullx.io/v1/predict"
        }
    
    def analyze_rugcheck(self, contract_address):
        try:
            response = requests.get(
                f"{self.endpoints['rugcheck']}/{contract_address}",
                headers={"Authorization": f"Bearer {self.config['api_keys']['rugcheck']}"}
            )
            return response.json().get('risk_score', 0)
        except Exception as e:
            logging.error(f"RugCheck error: {str(e)}")
            return 0

    def get_sentiment(self, symbol):
        try:
            response = requests.get(
                self.endpoints['tweetscout'],
                params={"symbol": symbol},
                headers={"X-API-KEY": self.config['api_keys']['tweetscout']}
            )
            return response.json().get('sentiment', 0)
        except Exception as e:
            logging.error(f"TweetScout error: {str(e)}")
            return 0

class TradingBot:
    def __init__(self, config):
        self.config = config
        self.api = APIClient(config)
        self.active_trades = {}
        self.running = False

    def analyze_token(self, token_data):
        if token_data['address'] in self.config['blacklists']['tokens']:
            return None
            
        analysis = {
            "rugcheck_score": self.api.analyze_rugcheck(token_data['address']),
            "sentiment": self.api.get_sentiment(token_data['symbol']),
            "volume_spike": token_data['volume_24h'] / token_data['volume_7d']
        }
        
        analysis['composite_score'] = self.calculate_score(analysis)
        return analysis

    def calculate_score(self, analysis):
        weights = {
            "rugcheck": 0.4,
            "sentiment": 0.3,
            "volume": 0.3
        }
        return (
            (analysis['rugcheck_score'] * weights['rugcheck']) +
            (analysis['sentiment'] * weights['sentiment']) +
            (analysis['volume_spike'] * weights['volume'])
        )

class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meme Coin Trading Bot")
        self.geometry("1200x800")
        self.config = ConfigManager()
        self.bot = TradingBot(self.config.config)
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Create notebook
        self.notebook = ttk.Notebook(self)
        
        # Monitoring Tab
        self.monitor_frame = ttk.Frame(self.notebook)
        self.create_monitor_tab()
        
        # Analysis Tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.create_analysis_tab()
        
        # Settings Tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.create_settings_tab()
        
        self.notebook.add(self.monitor_frame, text="Monitoring")
        self.notebook.add(self.analysis_frame, text="Analysis")
        self.notebook.add(self.settings_frame, text="Settings")
        self.notebook.pack(expand=True, fill=tk.BOTH)

    def create_monitor_tab(self):
        # Token list
        self.token_tree = ttk.Treeview(self.monitor_frame, columns=('Symbol', 'Price', 'Volume', 'Score'))
        for col in self.token_tree['columns']:
            self.token_tree.heading(col, text=col)
            self.token_tree.column(col, width=150)
        
        # Control buttons
        control_frame = ttk.Frame(self.monitor_frame)
        ttk.Button(control_frame, text="Start", command=self.start_monitoring).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Stop", command=self.stop_monitoring).pack(side=tk.LEFT)
        
        # Layout
        self.token_tree.pack(fill=tk.BOTH, expand=True)
        control_frame.pack()

    def create_analysis_tab(self):
        # Analysis components
        self.analysis_text = tk.Text(self.analysis_frame, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)

    def create_settings_tab(self):
        # API Key Management
        api_frame = ttk.LabelFrame(self.settings_frame, text="API Keys")
        ttk.Label(api_frame, text="RugCheck:").grid(row=0, column=0)
        self.rugcheck_entry = ttk.Entry(api_frame)
        self.rugcheck_entry.grid(row=0, column=1)
        
        # Load current values
        self.rugcheck_entry.insert(0, self.config.config['api_keys']['rugcheck'])
        
        # Save button
        ttk.Button(self.settings_frame, text="Save Config", command=self.save_config).pack()

    def start_monitoring(self):
        self.bot.running = True
        threading.Thread(target=self.monitor_loop).start()

    def stop_monitoring(self):
        self.bot.running = False

    def monitor_loop(self):
        while self.bot.running:
            try:
                # Replace with actual Pump.fun API call
                mock_data = [{
                    'symbol': 'MEME',
                    'address': '0x123...',
                    'price': 0.0012,
                    'volume_24h': 100000,
                    'volume_7d': 500000
                }]
                
                for token in mock_data:
                    analysis = self.bot.analyze_token(token)
                    if analysis and analysis['composite_score'] > self.config.config['thresholds']['risk_score']:
                        self.token_tree.insert('', 'end', values=(
                            token['symbol'],
                            token['price'],
                            token['volume_24h'],
                            f"{analysis['composite_score']:.2f}"
                        ))
                
                time.sleep(60)
            except Exception as e:
                logging.error(f"Monitoring error: {str(e)}")

    def save_config(self):
        self.config.config['api_keys']['rugcheck'] = self.rugcheck_entry.get()
        self.config.save_config()

    def on_close(self):
        self.bot.running = False
        self.destroy()

if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()
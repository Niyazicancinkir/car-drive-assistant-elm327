import csv
from datetime import datetime
from pathlib import Path

class TelemetryLogger:
    def __init__(self):
        self.current_file = None

    def start_new_log(self):
        filename = f"telemetry_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.current_file = Path(__file__).parent / filename
        
        with open(self.current_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Zaman", "RPM", "Hiz", "MotorYuku", "GazKelebegi", "AteslemeAvansi", "MAF",
                "Hararet", "EmmeSicaklik", "DisSicaklik", "Voltaj", "AtmosferBasinci", 
                "YakitSeviyesi", "AnlikTuketim", "STFT", "LTFT", "Lambda", "YagSicakligi", "CalismaSuresi"
            ])
        return self.current_file.name

    def log_data(self, data):
        if not self.current_file:
            return

        with open(self.current_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get("elapsed", 0), data.get("rpm", 0), data.get("speed", 0),
                data.get("load", 0), data.get("throttle", 0), data.get("spark", 0), data.get("maf", 0),
                data.get("coolant", 0), data.get("intake", 0), data.get("ambient", 0),
                data.get("voltage", 0), data.get("barometric", 0),
                data.get("fuel_lvl", 0), data.get("fuel_val", 0),
                data.get("short_trim", 0), data.get("long_trim", 0), data.get("lambda_val", 0),
                data.get("oil_temp", 0), data.get("run_time", 0)
            ])
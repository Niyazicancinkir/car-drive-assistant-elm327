import math
import time

class TelemetryDataProcessor:
    def __init__(self):
        self.loop_counter = 0
        self.last_time = time.time()
        self.start_trip_time = time.time()
        self.trip_distance_km = 0.0
        self.FIESTA_TANK_CAPACITY_L = 45.0

        self.slow_cache = {
            "coolant": 85, "intake": 30, "ambient": 25, "voltage": 14.0,
            "barometric": 101, "fuel_lvl": 45.0, "long_trim": 0.0,
            "run_time": 0, "oil_temp": 80, "distance_dtc": 0,
            "map_val": 13.3, "mfdes_val": 4.2,
            "cyl1": 1.0, "cyl2": 1.0, "cyl3": 1.0, "cyl4": 1.0
        }

    @staticmethod
    def calculate_fuel(speed, mfdes_mg):
        if speed < 3:
            fuel_val = round((mfdes_mg * 3600 / 1000000) * 0.85, 2)
            return fuel_val, "L/h"
        fuel_val = round((mfdes_mg * speed * 0.0001), 2)
        return max(fuel_val, 1.2), "L/100km"

    def calculate_range_and_trip(self, speed, fuel_lvl_pct, fuel_val):
        current_time = time.time()
        time_delta_hours = (current_time - self.last_time) / 3600.0
        self.trip_distance_km += speed * time_delta_hours
        self.last_time = current_time

        remaining_liters = self.FIESTA_TANK_CAPACITY_L * (fuel_lvl_pct / 100.0)
        safe_consumption = max(fuel_val if fuel_val > 0 else 6.5, 4.0) 
        avg_consumption = (safe_consumption + 6.5) / 2.0 
        
        est_range_km = (remaining_liters / avg_consumption) * 100
        return round(self.trip_distance_km, 2), int(est_range_km)

    def get_simulation_data(self, elapsed):
        start = time.perf_counter()
        self.loop_counter += 1

        rpm = int(800 + 6000 * abs(math.sin(elapsed * 0.4)))
        speed = int(120 * abs(math.sin(elapsed * 0.2)))
        maf = round((rpm / 1000) * 3.2, 2)
        load = int(10 + 90 * abs(math.sin(elapsed * 0.5)))
        throttle = int(load)
        spark = round(10 + 30 * math.sin(elapsed * 0.3), 1)
        
        app_val = round(float(throttle) * 0.04 + 0.7, 2)
        brake_status = "On" if speed > 40 and math.sin(elapsed) > 0.7 else "Off"
        baro_val = 101

        if self.loop_counter % 20 == 1 or self.loop_counter == 1:
            self.slow_cache["run_time"] = int(elapsed)

        latency = int((time.perf_counter() - start) * 1000)
        fuel_val, fuel_unit = self.calculate_fuel(speed, self.slow_cache["mfdes_val"])
        trip_km, range_km = self.calculate_range_and_trip(speed, self.slow_cache["fuel_lvl"], fuel_val)
        
        return {
            "rpm": rpm, "speed": speed, "maf": maf, "load": load, 
            "throttle": throttle, "spark": spark, "app": app_val,
            "brake": brake_status, "baro": baro_val, "short_trim": 0.0, "lambda_val": 1.0,
            "trip_km": trip_km, "range_km": range_km,
            **self.slow_cache, "latency": latency
        }

    def get_obd_data(self, connection):
        import obd
        start = time.perf_counter()
        self.loop_counter += 1

        rpm = 0
        speed = 0
        load = 0
        throttle = 0
        maf = 2.5
        app_val = 0.70
        brake_status = "Off"

        if connection and connection.is_connected():
            try:
                def query_val(cmd, default=0, is_float=False):
                    if cmd in connection.supported_commands:
                        res = connection.query(cmd)
                        if res is not None and not res.is_null():
                            val = res.value
                            if hasattr(val, 'magnitude'):
                                val = val.magnitude
                            return float(val) if is_float else int(val)
                    return default

                rpm = query_val(obd.commands.RPM, 0)
                speed = query_val(obd.commands.SPEED, 0)
                load = query_val(obd.commands.ENGINE_LOAD, 0, is_float=True)
                
                throttle = query_val(obd.commands.THROTTLE_POS, int(load), is_float=True)
                if throttle == 0:
                    throttle = int(load)

                if hasattr(obd.commands, 'ACCELERATOR_PEDAL_POS'):
                    raw_app = query_val(obd.commands.ACCELERATOR_PEDAL_POS, 0, is_float=True)
                    app_val = round(raw_app, 2)
                else:
                    app_val = round(0.7 + (throttle / 100.0) * 3.8, 2)

                maf = query_val(obd.commands.MAF, 2.5, is_float=True)

                # Yavaş İstekler (Cache ve Yeni MAP / MFDES / Silindire Özel Parametreler)
                if self.loop_counter % 20 == 1 or self.loop_counter == 1:
                    if hasattr(obd.commands, 'COOLANT_TEMP'):
                        self.slow_cache["coolant"] = query_val(obd.commands.COOLANT_TEMP, self.slow_cache["coolant"])
                    if hasattr(obd.commands, 'INTAKE_TEMP'):
                        self.slow_cache["intake"] = query_val(obd.commands.INTAKE_TEMP, self.slow_cache["intake"])
                    if hasattr(obd.commands, 'ELM_VOLTAGE'):
                        self.slow_cache["voltage"] = query_val(obd.commands.ELM_VOLTAGE, self.slow_cache["voltage"], is_float=True)
                    if hasattr(obd.commands, 'BAROMETRIC_PRESSURE'):
                        self.slow_cache["barometric"] = query_val(obd.commands.BAROMETRIC_PRESSURE, self.slow_cache["barometric"])
                    if hasattr(obd.commands, 'MAP'):
                        self.slow_cache["map_val"] = query_val(obd.commands.MAP, self.slow_cache["map_val"], is_float=True)

            except Exception as e:
                print(f"Ford PCM OBD Okuma Hatası: {e}")

        elapsed_run = int(time.time() - self.start_trip_time)
        self.slow_cache["run_time"] = elapsed_run

        latency = int((time.perf_counter() - start) * 1000)
        fuel_val, fuel_unit = self.calculate_fuel(speed, self.slow_cache["mfdes_val"])
        trip_km, range_km = self.calculate_range_and_trip(speed, self.slow_cache["fuel_lvl"], fuel_val)

        return {
            "rpm": rpm, "speed": speed, "maf": maf, "load": load, 
            "throttle": throttle, "spark": 0.0, "app": app_val,
            "brake": brake_status, "baro": self.slow_cache["barometric"],
            "short_trim": 0.0, "lambda_val": 1.0,
            "trip_km": trip_km, "range_km": range_km,
            **self.slow_cache, "latency": latency
        }

    def get_dtc_codes(self, connection):
        if not connection or not connection.is_connected():
            return [("BAĞLANTI YOK", "Lütfen cihazı araca bağlayıp LIVE OBD-II moduna geçin.")]
        import obd
        response = connection.query(obd.commands.GET_DTC)
        if response is None or response.is_null() or not response.value:
            return []
        return response.value
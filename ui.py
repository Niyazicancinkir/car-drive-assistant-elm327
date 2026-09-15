import glob
import os
import pandas as pd
import streamlit as st

class UIManager:
    @staticmethod
    def value(data, key, default=0):
        value = data.get(key, default)
        return default if value is None else value

    @staticmethod
    def create_gauge(value, title, maximum, thresholds, suffix=""):
        value = float(UIManager.value({"v": value}, "v", 0))
        value = max(0, min(value, maximum))
        percentage = (value / maximum) * 100

        if value <= thresholds[0]:
            bar_color = "linear-gradient(90deg, #16a34a, #22c55e)"; shadow = "#22c55e"
        elif value <= thresholds[1]:
            bar_color = "linear-gradient(90deg, #ca8a04, #eab308)"; shadow = "#eab308"
        elif value <= thresholds[2]:
            bar_color = "linear-gradient(90deg, #ea580c, #f97316)"; shadow = "#f97316"
        else:
            bar_color = "linear-gradient(90deg, #dc2626, #ef4444)"; shadow = "#ef4444"

        html = f"""
        <div style="background: #111c2f; border: 1px solid #263449; border-radius: 14px; padding: 20px; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px;">
                <span style="color: #93c5fd; font-size: 14px; font-weight: 700; text-transform: uppercase;">{title}</span>
                <span style="color: white; font-size: 28px; font-weight: 800; line-height: 1;">{int(value)}<span style="font-size: 14px; color: #94a3b8; font-weight: 500; margin-left: 4px;">{suffix}</span></span>
            </div>
            <div style="background: #0f172a; border-radius: 8px; height: 18px; width: 100%; border: 1px solid #1e293b; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
                <div style="background: {bar_color}; width: {percentage}%; height: 100%; border-radius: 6px; box-shadow: 0 0 12px {shadow};"></div>
            </div>
        </div>
        """
        return html

    @staticmethod
    def smooth(key, new_value, alpha=0.25):
        try:
            new_value = float(new_value)
        except (TypeError, ValueError):
            return new_value
        store = st.session_state.setdefault("_smoothed_values", {})
        previous = store.get(key)
        smoothed = new_value if previous is None else previous + (new_value - previous) * alpha
        store[key] = smoothed
        return round(smoothed, 1)

    @staticmethod
    def metric(box, label, value, delta=None, delta_color="normal"):
        with box:
            st.metric(label, value, delta=delta, delta_color=delta_color)

    @staticmethod
    def init_sidebar():
        st.set_page_config(page_title="Fiesta RS Telemetry", page_icon="🏎️", layout="wide")

        st.markdown(
            """
            <style>
                .stApp { background: #0b1120; color: white; }
                [data-testid="stSidebar"] { background: #111827; }
                [data-testid="stMetric"] { background: #111c2f; border: 1px solid #263449; border-radius: 14px; padding: 12px; min-height: 100px; }
                .header { background: linear-gradient(135deg, #172554, #0f172a); border: 1px solid #334155; border-radius: 16px; padding: 20px 25px; margin-bottom: 20px; }
                .header h1 { margin: 0; }
                .section { color: #93c5fd; font-size: 1.1rem; font-weight: bold; margin: 20px 0 10px; }
                .dtc-card { background: #7f1d1d; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #dc2626;}
            </style>
            """, unsafe_allow_html=True
        )

        st.sidebar.title("🧭 Menü")
        page = st.sidebar.radio("Sayfa Seçimi", ["🏎️ Canlı Kokpit", "🩺 Arıza Teşhis (DTC)"])
        st.sidebar.divider()

        st.sidebar.title("🛠️ Kontrol Paneli")
        mode = st.sidebar.selectbox("Bağlantı Modu", ["SIMULATION", "LIVE OBD-II", "REPLAY (Geçmiş Sürüş)"])
        com_port = st.sidebar.text_input("COM Port", "COM3")
        baud_rate = st.sidebar.selectbox("Baud Rate", [38400, 115200, 9600])

        replay_file = None
        if mode == "REPLAY (Geçmiş Sürüş)":
            files = glob.glob("telemetry_log_*.csv")
            if files:
                files.sort(key=os.path.getmtime, reverse=True)
                replay_file = st.sidebar.selectbox("Kayıt Seçin", files)
            else:
                st.sidebar.warning("Kayıt dosyası bulunamadı.")

        return page, mode, com_port, baud_rate, replay_file

    @staticmethod
    def init_cockpit_ui():
        start_btn = st.sidebar.button("▶ Başlat / Durdur", use_container_width=True)

        st.markdown('<div class="header"><h1>🏎️ Fiesta RS Telemetri</h1><p>Motor ve araç verilerini anlık olarak takip edin.</p></div>', unsafe_allow_html=True)
        ui = {}
        def card(column): return column.container(border=True).empty()

        st.markdown('<div class="section">🚗 Sürüş Özeti</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="large")
        ui["gauge_rpm"] = c1.empty()
        ui["gauge_speed"] = c2.empty()
        ui["gauge_throttle"] = c3.empty()

        st.markdown('<div class="section">⚡ Performans ve Sürücü Girdileri</div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5 = st.columns(5)
        ui["load"] = card(p1)
        ui["fuel_inst"] = card(p2)
        ui["app_pos"] = card(p3)   
        ui["brake_status"] = card(p4)
        ui["latency"] = card(p5)

        st.markdown('<div class="section">🌡️ Sistem ve Çevre</div>', unsafe_allow_html=True)
        s1, s2, s3, s4, s5 = st.columns(5)
        ui["coolant"] = card(s1)
        ui["intake"] = card(s2)
        ui["ambient"] = card(s3)
        ui["voltage"] = card(s4)
        ui["baro"] = card(s5)

        tab_diagnostic, tab_charts = st.tabs(["📊 Genişletilmiş Veriler", "📈 Grafikler"])

        with tab_diagnostic:
            st.markdown("##### 🔍 Ford PCM Detaylı Sensörler ve Silindir Dengeleri")
            d1, d2, d3, d4, d5 = st.columns(5)
            ui["map_val"] = card(d1)
            ui["mfdes_val"] = card(d2)
            ui["short_trim"] = card(d3)
            ui["long_trim"] = card(d4)
            ui["run_time"] = card(d5)

            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            ui["cyl1"] = card(sc1)
            ui["cyl2"] = card(sc2)
            ui["cyl3"] = card(sc3)
            ui["cyl4"] = card(sc4)
            ui["lambda"] = card(sc5)

        with tab_charts:
            g1, g2 = st.columns(2)
            ui["chart_main"] = card(g1)
            ui["chart_load"] = card(g2)

        return start_btn, ui

    @staticmethod
    def update_ui(ui, data, history):
        rpm = UIManager.smooth("rpm", UIManager.value(data, "rpm"))
        speed = UIManager.smooth("speed", UIManager.value(data, "speed"))
        throttle = UIManager.smooth("throttle", UIManager.value(data, "throttle"))

        ui["gauge_rpm"].markdown(UIManager.create_gauge(rpm, "MOTOR DEVRİ", 7000, [3500, 5000, 6200], " RPM"), unsafe_allow_html=True)
        ui["gauge_speed"].markdown(UIManager.create_gauge(speed, "HIZ", 220, [80, 120, 160], " km/h"), unsafe_allow_html=True)
        ui["gauge_throttle"].markdown(UIManager.create_gauge(throttle, "GAZ KEB.", 100, [40, 70, 90], " %"), unsafe_allow_html=True)

        latency = UIManager.value(data, "latency")
        coolant = UIManager.smooth("coolant", UIManager.value(data, "coolant"))
        voltage = UIManager.smooth("voltage", UIManager.value(data, "voltage"))
        brake_txt = "BASILI" if UIManager.value(data, "brake", "Off") == "On" else "SERBEST"

        UIManager.metric(ui["load"], "Motor Yükü", f"%{UIManager.value(data, 'load')}")
        UIManager.metric(ui["fuel_inst"], "Anlık Tüketim", f"{UIManager.value(data, 'fuel_val')} {data.get('fuel_unit', '')}")
        UIManager.metric(ui["app_pos"], "Gaz Pedalı (APP)", f"{UIManager.value(data, 'app')} V")
        UIManager.metric(ui["brake_status"], "Fren (BKS)", brake_txt)
        UIManager.metric(ui["latency"], "OBD Gecikmesi", f"{latency} ms", "İyi" if latency < 75 else "Zayıf", "normal" if latency < 75 else "inverse")

        UIManager.metric(ui["coolant"], "Hararet", f"{coolant} °C", "Normal" if coolant <= 95 else "UYARI", "normal" if coolant <= 95 else "inverse")
        UIManager.metric(ui["intake"], "Emme Sıcaklığı", f"{UIManager.value(data, 'intake')} °C")
        UIManager.metric(ui["ambient"], "Hava Basıncı", f"{UIManager.value(data, 'baro')} kPa")
        UIManager.metric(ui["voltage"], "Akü Voltajı", f"{voltage} V", "Normal" if voltage >= 12.5 else "Düşük", "normal" if voltage >= 12.5 else "inverse")
        UIManager.metric(ui["baro"], "Atmosfer Basıncı", f"{UIManager.value(data, 'barometric')} kPa")

        # Genişletilmiş Veriler Sekmesi Güncellemesi
        UIManager.metric(ui["map_val"], "Emme Basıncı (MAP)", f"{UIManager.value(data, 'map_val')} kPa")
        UIManager.metric(ui["mfdes_val"], "İstenen Yakıt (MFDES)", f"{UIManager.value(data, 'mfdes_val')} mg")
        UIManager.metric(ui["short_trim"], "Depo Doluluk", f"%{UIManager.value(data, 'fuel_lvl')}")
        UIManager.metric(ui["long_trim"], "Tahmini Menzil", f"{data.get('range_km', 0)} km")
        
        UIManager.metric(ui["cyl1"], "Silindir 1 Denge", f"{UIManager.value(data, 'cyl1')} mg")
        UIManager.metric(ui["cyl2"], "Silindir 2 Denge", f"{UIManager.value(data, 'cyl2')} mg")
        UIManager.metric(ui["cyl3"], "Silindir 3 Denge", f"{UIManager.value(data, 'cyl3')} mg")
        UIManager.metric(ui["cyl4"], "Silindir 4 Denge", f"{UIManager.value(data, 'cyl4')} mg")
        UIManager.metric(ui["lambda"], "Sürüş (Trip)", f"{data.get('trip_km', 0)} km")

        runtime = int(data.get("run_time", 0))
        hours, remainder = divmod(runtime, 3600)
        minutes, seconds = divmod(remainder, 60)
        UIManager.metric(ui["run_time"], "Çalışma", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        history.append(data.copy())
        del history[:-40]

        if not history: return

        df = pd.DataFrame(history)
        if "elapsed" in df.columns: df = df.set_index("elapsed")

        main_chart = df[["speed"]].copy()
        main_chart["RPM x100"] = df["rpm"] / 100
        with ui["chart_main"]:
            st.caption("Hız ve Devir Trendi")
            st.line_chart(main_chart, height=280)

        load_chart = df[["throttle", "load"]].copy()
        with ui["chart_load"]:
            st.caption("Gaz Kelebeği ve Motor Yükü")
            st.line_chart(load_chart, height=280)
import streamlit as st
import time
import pandas as pd
from audio import AudioAlertManager
from telemetry import TelemetryDataProcessor
from ui import UIManager
from logger import TelemetryLogger

def connect_obd(com_port, baud_rate):
    try:
        import obd
        return obd.OBD(portstr=com_port, baudrate=baud_rate, fast=True)
    except Exception as e:
        st.error(f"OBD Hatası: {e}")
        return None

def main():
    page, mode, com_port, baud_rate, replay_file = UIManager.init_sidebar()
    
    if "audio_manager" not in st.session_state:
        st.session_state.audio_manager = AudioAlertManager()
    if "logger" not in st.session_state:
        st.session_state.logger = TelemetryLogger()
    if "processor" not in st.session_state:
        st.session_state.processor = TelemetryDataProcessor()
    
    # SAYFA 1: KOKPİT EKRANI
    if page == "🏎️ Canlı Kokpit":
        start_btn, ui = UIManager.init_cockpit_ui()

        if start_btn:
            st.session_state["running"] = not st.session_state.get("running", False)
            if st.session_state["running"]:
                if mode != "REPLAY (Geçmiş Sürüş)":
                    csv_filename = st.session_state.logger.start_new_log()
                    st.sidebar.success(f"Log Kaydı Başladı: {csv_filename}")
                else:
                    st.sidebar.info(f"Oynatılıyor: {replay_file}")

        if st.session_state.get("running", False):
            t0 = time.time()
            history_data = []
            connection = connect_obd(com_port, baud_rate) if mode == "LIVE OBD-II" else None
            
            replay_df = pd.read_csv(replay_file) if mode == "REPLAY (Geçmiş Sürüş)" and replay_file else None
            replay_index = 0

            while st.session_state.get("running", False):
                if mode == "REPLAY (Geçmiş Sürüş)":
                    if replay_df is not None and replay_index < len(replay_df):
                        row = replay_df.iloc[replay_index]
                        raw_data = {
                            "rpm": int(row.get("RPM", 0)), "speed": int(row.get("Hiz", 0)),
                            "load": int(row.get("MotorYuku", 0)), "throttle": int(row.get("GazKelebegi", 0)),
                            "spark": float(row.get("AteslemeAvansi", 0.0)), "maf": float(row.get("MAF", 0.0)),
                            "coolant": int(row.get("Hararet", 0)), "intake": int(row.get("EmmeSicaklik", 0)),
                            "ambient": int(row.get("DisSicaklik", 0)), "voltage": float(row.get("Voltaj", 0.0)),
                            "barometric": int(row.get("AtmosferBasinci", 0)), "fuel_lvl": float(row.get("YakitSeviyesi", 0.0)),
                            "latency": 0
                        }
                        elapsed = row.get("Zaman", 0)
                        replay_index += 1
                    else:
                        st.success("Sürüş tekrarı tamamlandı.")
                        st.session_state["running"] = False
                        break
                else:
                    elapsed = time.time() - t0
                    if mode == "SIMULATION":
                        raw_data = st.session_state.processor.get_simulation_data(elapsed)
                    else:
                        raw_data = st.session_state.processor.get_obd_data(connection)
                    
                fuel_val, fuel_unit = TelemetryDataProcessor.calculate_fuel(raw_data["speed"], raw_data["maf"])
                trip_km, range_km = st.session_state.processor.calculate_range_and_trip(raw_data["speed"], raw_data.get("fuel_lvl", 0), fuel_val)

                data_dict = {
                    "elapsed": round(elapsed, 1),
                    "fuel_val": fuel_val, "fuel_unit": fuel_unit,
                    "trip_km": trip_km, "range_km": range_km,
                    **raw_data
                }

                if mode != "REPLAY (Geçmiş Sürüş)":
                    st.session_state.logger.log_data(data_dict)
                    if data_dict["rpm"] > 3000:
                        st.session_state.audio_manager.play()

                UIManager.update_ui(ui, data_dict, history_data)
                time.sleep(0.1)

    # SAYFA 2: ARIZA TEŞHİS (DTC) EKRANI
    elif page == "🩺 Arıza Teşhis (DTC)":
        st.title("🩺 OBD-II Arıza Teşhis Merkezi")
        st.info("⚠️ Veri bütünlüğünü korumak (Freeze-Frame verilerinin silinmemesi) amacıyla, bu araç sürümünde hata kodlarına müdahale yetkisi kapatılmıştır. Yalnızca Salt-Okunur (Read-Only) tarama yapılabilir.")
        
        if st.button("🔍 Hata Kodlarını Tara (Scan DTC)", use_container_width=True, type="primary"):
            with st.spinner("ECU taranıyor... Lütfen bekleyin."):
                connection = connect_obd(com_port, baud_rate) if mode == "LIVE OBD-II" else None
                
                if mode == "SIMULATION":
                    time.sleep(1)
                    dtc_list = [("P0104", "Kütle veya Hacim Hava Akışı Devresi Kesintili (Simülasyon)"), 
                                ("P0420", "Katalizör Sistemi Verimliliği Sınırın Altında (Simülasyon)")]
                else:
                    dtc_list = st.session_state.processor.get_dtc_codes(connection)
                
                if not dtc_list:
                    st.success("✅ Harika! Araç beyninde kayıtlı hiçbir hata kodu bulunamadı.")
                else:
                    st.error(f"🚨 {len(dtc_list)} adet hata kodu bulundu!")
                    for code, desc in dtc_list:
                        st.markdown(f"<div class='dtc-card'><h3>{code}</h3><p>{desc}</p></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
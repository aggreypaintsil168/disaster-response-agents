import os
import random
import time

import spade
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour


# ----------------------------
# DISASTER RULES (thresholds)
# ----------------------------
THRESHOLDS = {
    "FLOOD": {"water_cm": 50},
    "LANDSLIDE": {"rain_mm_hr": 30, "slope_deg": 30, "soil_moisture": 0.75},
    "EARTHQUAKE": {"magnitude": 5.0},
    # Very simple windstorm signals (good enough for Lab 2 simulation)
    "TYPHOON": {"wind_kmh": 118, "pressure_hpa": 950},
    "HURRICANE": {"wind_kmh": 119, "pressure_hpa": 980},
    "VOLCANIC_ERUPTION": {"ashfall_mm": 5, "so2_ppm": 2.0, "tremor_index": 0.6},
}


def detect_disasters(m):
    """
    Decide which disaster(s) are happening based on measurements m.
    Returns a list of disaster names.
    """
    detected = []

    # Flood
    if m["water_cm"] >= THRESHOLDS["FLOOD"]["water_cm"]:
        detected.append("FLOOD")

    # Landslide (rain + slope + soil moisture)
    if (
        m["rain_mm_hr"] >= THRESHOLDS["LANDSLIDE"]["rain_mm_hr"]
        and m["slope_deg"] >= THRESHOLDS["LANDSLIDE"]["slope_deg"]
        and m["soil_moisture"] >= THRESHOLDS["LANDSLIDE"]["soil_moisture"]
    ):
        detected.append("LANDSLIDE")

    # Earthquake
    if m["quake_magnitude"] >= THRESHOLDS["EARTHQUAKE"]["magnitude"]:
        detected.append("EARTHQUAKE")

    # Typhoon / Hurricane
    # We keep both as separate labels for your requirement.
    if m["wind_kmh"] >= THRESHOLDS["TYPHOON"]["wind_kmh"] and m["pressure_hpa"] <= THRESHOLDS["TYPHOON"]["pressure_hpa"]:
        detected.append("TYPHOON")
    elif m["wind_kmh"] >= THRESHOLDS["HURRICANE"]["wind_kmh"] and m["pressure_hpa"] <= THRESHOLDS["HURRICANE"]["pressure_hpa"]:
        detected.append("HURRICANE")

    # Volcanic eruption
    if (
        m["ashfall_mm"] >= THRESHOLDS["VOLCANIC_ERUPTION"]["ashfall_mm"]
        and m["so2_ppm"] >= THRESHOLDS["VOLCANIC_ERUPTION"]["so2_ppm"]
        and m["tremor_index"] >= THRESHOLDS["VOLCANIC_ERUPTION"]["tremor_index"]
    ):
        detected.append("VOLCANIC_ERUPTION")

    return detected


def severity_level(disasters, m):
    """
    Convert detected disasters + measurement intensity into LOW/MODERATE/HIGH/CRITICAL.
    """
    score = 0

    # Flood intensity
    if m["water_cm"] >= 80:
        score += 2
    elif m["water_cm"] >= 50:
        score += 1

    # Landslide intensity
    if m["rain_mm_hr"] >= 50:
        score += 2
    elif m["rain_mm_hr"] >= 30:
        score += 1
    if m["soil_moisture"] >= 0.85:
        score += 1

    # Earthquake intensity
    if m["quake_magnitude"] >= 6.5:
        score += 2
    elif m["quake_magnitude"] >= 5.0:
        score += 1

    # Windstorm intensity
    if m["wind_kmh"] >= 170:
        score += 2
    elif m["wind_kmh"] >= 119:
        score += 1
    if m["pressure_hpa"] <= 940:
        score += 1

    # Volcanic intensity
    if m["ashfall_mm"] >= 20:
        score += 2
    elif m["ashfall_mm"] >= 5:
        score += 1
    if m["so2_ppm"] >= 5.0:
        score += 1

    # If nothing detected, keep LOW
    if not disasters:
        score = 0

    if score >= 5:
        return "CRITICAL"
    if score >= 3:
        return "HIGH"
    if score >= 1:
        return "MODERATE"
    return "LOW"


def format_log(ts, disasters, severity, m):
    d = ",".join(disasters) if disasters else "NONE"
    return (
        f"{ts} | disasters={d:<35} | severity={severity:<8} | "
        f"water_cm={m['water_cm']:5.1f} | rain_mm_hr={m['rain_mm_hr']:5.1f} | "
        f"slope_deg={m['slope_deg']:4.1f} | soil_moisture={m['soil_moisture']:.2f} | "
        f"quake_mag={m['quake_magnitude']:.2f} | wind_kmh={m['wind_kmh']:6.1f} | "
        f"pressure_hpa={m['pressure_hpa']:6.1f} | ashfall_mm={m['ashfall_mm']:5.1f} | "
        f"so2_ppm={m['so2_ppm']:.2f} | tremor_idx={m['tremor_index']:.2f}"
    )


class SensorAgent(Agent):
    class MonitorBehaviour(PeriodicBehaviour):
        async def run(self):
            # 1) PERCEIVE: simulate environment measurements
            m = {
                "water_cm": random.uniform(0, 100),
                "rain_mm_hr": random.uniform(0, 70),
                "slope_deg": random.uniform(0, 45),
                "soil_moisture": random.uniform(0.20, 0.95),
                "quake_magnitude": random.uniform(2.0, 7.5),
                "wind_kmh": random.uniform(0, 220),
                "pressure_hpa": random.uniform(900, 1020),
                "ashfall_mm": random.uniform(0, 30),
                "so2_ppm": random.uniform(0.0, 8.0),
                "tremor_index": random.uniform(0.0, 1.0),
            }

            # 2) INTERPRET: detect disaster(s) and compute severity
            disasters = detect_disasters(m)
            severity = severity_level(disasters, m)

            # 3) LOG: timestamp + disasters + essential measurements
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            line = format_log(ts, disasters, severity, m)

            print(line)

            os.makedirs("logs", exist_ok=True)
            with open("logs/lab2_events.log", "a", encoding="utf-8") as f:
                f.write(line + "\n")

    async def setup(self):
        print(f"[{self.jid}] ✅ SensorAgent started (Lab 2).")
        print("Perception cycle: every 3 seconds")
        print("Logging to logs/lab2_events.log\n")
        self.add_behaviour(self.MonitorBehaviour(period=3))


async def main():
    jid = "aggreyfynn08@xmpp.jp"
    password = "045@Ghttp1007"  # put your real password here locally

    agent = SensorAgent(jid, password)
    await agent.start()

    # Keep agent alive
    while agent.is_alive():
        await spade.sleep(1)


if __name__ == "__main__":
    spade.run(main())

# KSP Maneuver Planner with Save/Load (.kmn files)
# No external libraries

import math

KERBIN_RADIUS = 600_000.0
KERBIN_MU = 3.5316e12
MUN_ORBIT_RADIUS = 12_000_000.0
G0 = 9.80665

def calculate_mun_transfer(orbit_alt_km, mass, thrust, isp):
    r1 = KERBIN_RADIUS + orbit_alt_km * 1000
    r2 = MUN_ORBIT_RADIUS

    v_circular = math.sqrt(KERBIN_MU / r1)
    v_transfer = math.sqrt(
        KERBIN_MU * (2 / r1 - 1 / ((r1 + r2) / 2))
    )

    delta_v = v_transfer - v_circular

    mass_flow = thrust / (isp * G0)
    burn_time = mass * (1 - math.exp(-delta_v / (isp * G0))) / mass_flow

    return delta_v, burn_time

def save_maneuver(filename, data):
    with open(filename, "w") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")
    print(f"\nManeuver saved to '{filename}'")

def load_maneuver(filename):
    data = {}
    with open(filename, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                data[key] = value
    return data

# ---------------- MAIN PROGRAM ----------------

print("\nKSP Maneuver Planner")
print("====================")
print("1 - Create new Mun transfer maneuver")
print("2 - Load maneuver from .kmn file")

choice = input("\nChoose an option (1 or 2): ")

if choice == "1":
    name = input("Maneuver name: ")
    orbit_alt = float(input("Kerbin orbit altitude (km): "))
    mass = float(input("Vessel mass at burn (kg): "))
    thrust = float(input("Total thrust (N): "))
    isp = float(input("Engine ISP (s): "))

    delta_v, burn_time = calculate_mun_transfer(
        orbit_alt, mass, thrust, isp
    )

    print("\n===== Maneuver Results =====")
    print(f"Δv required: {delta_v:.1f} m/s")
    print(f"Burn time: {burn_time:.1f} s")
    print(f"Start burn {burn_time/2:.1f} s before node")

    notes = input("\nOptional notes: ")

    save = input("Save this maneuver? (y/n): ").lower()
    if save == "y":
        filename = input("Filename (example: mun_transfer.kmn): ")
        maneuver_data = {
            "MANEUVER_NAME": name,
            "ORBIT_ALTITUDE_KM": orbit_alt,
            "DELTA_V": round(delta_v, 2),
            "BURN_TIME": round(burn_time, 2),
            "THRUST": thrust,
            "ISP": isp,
            "NOTES": notes
        }
        save_maneuver(filename, maneuver_data)

elif choice == "2":
    filename = input("Enter .kmn filename to load: ")
    data = load_maneuver(filename)

    print("\n===== Loaded Maneuver =====")
    for key, value in data.items():
        print(f"{key}: {value}")

    if "BURN_TIME" in data:
        half = float(data["BURN_TIME"]) / 2
        print(f"\nStart burn {half:.1f} s before node")

else:
    print("Invalid option.")


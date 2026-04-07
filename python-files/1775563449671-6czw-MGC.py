# ================================
# Interaktivni kalkulator MGC
# ================================

print("=== Motor Gearing Capability Calculator ===\n")

# 1️⃣ Degraded Torque Factor (DEGTRQ)
while True:
    motor_voltage_type = input("Unesi motor voltage type AC / DC: ").strip().upper()
    if motor_voltage_type == "AC":
        degraded_voltage_exp = 2
        break
    elif motor_voltage_type == "DC":
        degraded_voltage_exp = 1
        break
    else:
        print("Krivi unos, unesi AC ili DC")

# 2️⃣ Unos napona motora
while True:
    try:
        voltage_motor_rated = float(input("Unesi motor rated voltage [V]: "))
        voltage_motor_terminal = float(input("Unesi motor terminal voltage [V]: "))
        break
    except ValueError:
        print("Molim unesite broj.")

degraded_torque_factor = (voltage_motor_terminal / voltage_motor_rated) ** degraded_voltage_exp
print(f"Degraded Torque Factor (DEGTRQ) = {degraded_torque_factor:.4f}\n")

# 3️⃣ Temperature Degradation Factor (DVF)
while True:
    try:
        max_area_temperature = float(input("Unesi max area temperature [°C]: "))
        motor_rated_reduction = float(input("Unesi motor rated reduction [%]: "))
        break
    except ValueError:
        print("Molim unesite broj.")

temperature_degradation_factor = 1 - (((max_area_temperature - 25) / 155) * (motor_rated_reduction / 100))
print(f"Temperature Degradation Factor (DVF) = {temperature_degradation_factor:.4f}\n")

# 4️⃣ Unos ostalih parametara
def unos_podatka(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Molim unesite broj!")

motor_torque_rate = unos_podatka("Unesi motor torque rate: ")
actuator_oar = unos_podatka("Unesi actuator OAR: ")

pullout_efficiency = 0.6  # EFFP
application_factor = 0.9   # AF

# 5️⃣ Izračun MGC
motor_gearing_capability = (
    motor_torque_rate
    * actuator_oar
    * pullout_efficiency
    * application_factor
    * temperature_degradation_factor
    * degraded_torque_factor
)

# 6️⃣ Ispis rezultata
print("\n=== Rezultati ===")
print(f"Motor Torque Rate = {motor_torque_rate}")
print(f"Actuator OAR = {actuator_oar}")
print(f"Pullout Efficiency (EFFP) = {pullout_efficiency}")
print(f"Application Factor (AF) = {application_factor}")
print(f"Temperature Degradation Factor (DVF) = {temperature_degradation_factor:.4f}")
print(f"Degraded Torque Factor (DEGTRQ) = {degraded_torque_factor:.4f}")
print(f"\nMotor Gearing Capability (MGC) = {motor_gearing_capability:.4f}")

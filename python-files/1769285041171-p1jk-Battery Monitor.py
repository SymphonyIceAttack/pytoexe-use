# %%
import plyer
import batteryinfo
from matplotlib.pyplot import title
from notify2 import appname

battery=batteryinfo.Battery()
while True:
    if battery.state=="Full":
        plyer.notification.notify(
            appname="Battery Monitor",
            title = "Battery Full",
            message = "Battery Temp: " + str(battery.temperature) + "\nTo Empty: "+str(battery.time_to_empty)+"\nVoltage: "+str(battery.voltage)+"V",
            timeout=10,
            toast=False,
        )
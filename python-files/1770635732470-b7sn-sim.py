import serial
import vgamepad as vg
import time

COM_PORT = "COM3"  # Change to your Arduino port
BAUDRATE = 115200

ser = serial.Serial(COM_PORT, BAUDRATE, timeout=1)
time.sleep(2)  # Arduino reset

gamepad = vg.VX360Gamepad()

def map_range(val, in_min, in_max, out_min, out_max):
    val = max(in_min, min(in_max, val))
    return int((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

print("Sim controller running...")

while True:
    try:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        # wheel, throttle, brake, paddleUp, paddleDown, nitro, speedBrake, btn3
        wheel, throttle, brake, paddleUp, paddleDown, nitro, speedBrake, btn3 = map(int, line.split(","))

        # ---- STEERING ----
        steer = map_range(wheel, -512, 512, -16384, 16384)
        gamepad.left_joystick(x_value=steer, y_value=map_range(throttle, 0, 1023, 0, 16384))
        # ---- PEDALS ----
        gamepad.left_trigger(map_range(brake, 0, 1023, 0, 255))

        # ---- BUTTONS ----
        buttons = {
            vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER: paddleDown,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER: paddleUp,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_X: nitro,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_B: speedBrake,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_A: btn3
        }

        for button, state in buttons.items():
            if state:
                gamepad.press_button(button)
            else:
                gamepad.release_button(button)

        gamepad.update()

    except Exception as e:
        print("Error:", e)

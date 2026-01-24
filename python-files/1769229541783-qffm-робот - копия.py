
import serial
import keyboard

ser=serial.Serial('COM24',9600)


def up():
    ser.write(b'F')
def down():
    ser.write(b'B')
def right():
    ser.write(b'R')
def left():
    ser.write(b'L')
def leftu():
    ser.write(b'G')
def downr():
    ser.write(b'J')
def leftd():
    ser.write(b'I')
def upr():
    ser.write(b'H')
def stop():
    ser.write(b'S')
def bump():
    ser.write(b'Y')

while True:
    x=keyboard.read_key()
    
    if x == "ц":
        up()
    elif x == "ы":
        down()
    elif x == "ф":
        left()
    elif x == "в":
        right()
    elif x == "е":
        bump()
    elif x == "space":
        stop()



import pymem # type: ignore
import pymem.process # type: ignore
import keyboard
import time

# ������� (���������, ����� �������� ��� ���������� ������ ����!)
# ���������� ����� ����� �� GitHub: a2x/cs2-dumper
dwLocalPlayerPawn = 0x2065AF0
m_fFlags = 0x400 

def main():
    try:
        # ������������ � CS2
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        
        print("������ �������. ��������� ������ ��� Bhop.")

        while True:
            # ���� ����� ������
            if keyboard.is_pressed('space'):
                # �������� ����� ���������� ������
                player = pm.read_longlong(client + dwLocalPlayerPawn)
                
                if player:
                    # ������ ����� ������ (�� ����� ��� � �������)
                    # 65665 / 65667 � ������ �������� ���������� �� �����
                    fFlags = pm.read_int(player + m_fFlags)
                    
                    # ���� �� ����� (���� 1 - �� �����)
                    if fFlags & (1 << 0):
                        # ��������� ������� ������
                        # � CS2 ����� ����� ������������ ������ � ������ ��� +jump
                        # �� ��� ������� ����� ����������� ������� �������
                        keyboard.press_and_release('space')
                        
            time.sleep(0.01) # ����� �� ��������� ���������

    except Exception as e:
        print(f"������: {e}")

if __name__ == "__main__":
    main()

import pymem
import pymem.process
import time
import keyboard

# 吸怪配置
ENABLE_KEY = 'F8'      # 开启吸怪
DISABLE_KEY = 'F9'     # 关闭吸怪
TELEPORT_DISTANCE = 1.5

is_running = False
print("===== 全图吸怪工具 =====")
print(f"F8 = 开启吸怪")
print(f"F9 = 关闭吸怪")
print("========================")

def main():
    global is_running
    try:
        pm = pymem.Pymem("Warframe.x64.exe")
    except:
        print("未找到 Warframe 游戏进程！")
        return

    while True:
        if keyboard.is_pressed(ENABLE_KEY):
            is_running = True
            print("✅ 吸怪已开启（F8）")
            time.sleep(0.3)

        if keyboard.is_pressed(DISABLE_KEY):
            is_running = False
            print("❌ 吸怪已关闭（F9）")
            time.sleep(0.3)

        if not is_running:
            time.sleep(0.01)
            continue

        try:
            # 吸怪逻辑（全图怪物拉到玩家身边）
            player_base = pm.read_longlong(pm.base_address + 0x038A28E0)
            player_pos = [
                pm.read_float(player_base + 0x40),
                pm.read_float(player_base + 0x44),
                pm.read_float(player_base + 0x48)
            ]

            enemy_count = pm.read_int(player_base + 0xA8)
            enemy_list = pm.read_longlong(player_base + 0xB0)

            for i in range(enemy_count):
                enemy_ptr = pm.read_longlong(enemy_list + i * 0x8)
                if enemy_ptr:
                    pm.write_float(enemy_ptr + 0x40, player_pos[0])
                    pm.write_float(enemy_ptr + 0x44, player_pos[1] + TELEPORT_DISTANCE)
                    pm.write_float(enemy_ptr + 0x48, player_pos[2])
        except:
            pass

        time.sleep(0.02)

if __name__ == "__main__":
    main()
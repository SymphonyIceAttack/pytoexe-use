# -*- coding: utf-8 -*-
# Trove x64 实体读取器
# 保存为 Trove_Reader.py 直接运行

import math
import time
import os
import ctypes

# 自动请求管理员权限
try:
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "python.exe", __file__, None, 1)
        exit()
except:
    pass

# 导入pymem
try:
    import pymem
    import pymem.process
except ImportError:
    print("正在安装 pymem...")
    os.system("pip install pymem -q")
    import pymem
    import pymem.process

# ============= 配置 =============
PROCESS_NAME = "Trove_x64.exe"
OWNER_RVA = 0x1396BC0
REFRESH_RATE = 0.5  # 秒

# 全局变量
player_x = player_y = player_z = 0

# ============= 工具函数 =============
def read_ptr(pm, address):
    """安全读取64位指针"""
    try:
        value = pm.read_ulonglong(address)
        if 0x10000 <= value <= 0x00007FFFFFFFFFFF:
            return value
    except:
        pass
    return 0

# ============= 主程序 =============
def main():
    os.system("title Trove x64 实体读取器")
    os.system('cls')
    
    print("=" * 70)
    print("  🎮 Trove x64 实体读取器")
    print("=" * 70)
    print("🔍 正在连接 Trove_x64.exe...")
    
    # 连接游戏
    try:
        pm = pymem.Pymem(PROCESS_NAME)
        module = pymem.process.module_from_name(pm.process_handle, PROCESS_NAME)
        module_base = module.lpBaseOfDll
        owner = read_ptr(pm, module_base + OWNER_RVA)
        
        if not owner:
            raise Exception("Owner指针无效")
            
        print(f"✅ 连接成功!")
        print(f"   模块基址: 0x{module_base:X}")
        print(f"   Owner: 0x{owner:X}")
        time.sleep(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("\n请确保:")
        print("  1. Trove_x64.exe 正在运行")
        print("  2. 以管理员身份运行")
        input("\n按回车键退出...")
        return

    # 主循环
    while True:
        try:
            # 读取哈希桶头
            base = read_ptr(pm, owner + 0xE0)
            stride = pm.read_ulonglong(owner + 0xE8)
            count = pm.read_ulonglong(owner + 0xF0)
            
            entities = []
            seen_nodes = set()
            seen_objects = set()
            
            # 遍历所有桶
            for bucket_idx in range(min(count, 3000)):
                node = base + bucket_idx * stride
                depth = 0
                
                while node and node not in seen_nodes and depth < 64:
                    seen_nodes.add(node)
                    
                    # 读next指针，清除标记位
                    next_raw = read_ptr(pm, node)
                    next_node = next_raw & 0xFFFFFFFFFFFFFFFE
                    
                    # 读实体对象
                    obj = read_ptr(pm, node + 0x10)
                    
                    if obj and obj not in seen_objects:
                        seen_objects.add(obj)
                        
                        # ========== 读名字 ==========
                        name_ptr1 = read_ptr(pm, obj + 0x98)
                        name_ptr = read_ptr(pm, name_ptr1)
                        
                        if name_ptr:
                            try:
                                name_bytes = pm.read_bytes(name_ptr, 64)
                                null_pos = name_bytes.find(b'\x00')
                                if null_pos > 0:
                                    name = name_bytes[:null_pos].decode('utf-8', errors='ignore')
                                    
                                    # 只显示NPC
                                    if name.startswith('npc/'):
                                        # ========== 读坐标 ==========
                                        component_vec = read_ptr(pm, obj + 0x130)
                                        if component_vec:
                                            pos_object = read_ptr(pm, component_vec + 0x8)
                                            if pos_object:
                                                x = pm.read_float(pos_object + 0xD0)
                                                y = pm.read_float(pos_object + 0xD4)
                                                z = pm.read_float(pos_object + 0xD8)
                                                
                                                # ========== 读血量 ==========
                                                health_obj = read_ptr(pm, component_vec + 0x108)
                                                health = pm.read_double(health_obj + 0xD8) if health_obj else 0
                                                
                                                # ========== 读等级 ==========
                                                level_obj = read_ptr(pm, component_vec + 0xA8)
                                                level = pm.read_uint(level_obj + 0x208) if level_obj else 0
                                                
                                                entities.append({
                                                    'name': name[4:],  # 去掉 npc/
                                                    'health': health,
                                                    'level': level,
                                                    'x': x, 'y': y, 'z': z
                                                })
                            except:
                                pass
                    
                    # 链表结束条件
                    if next_raw == 1 or not next_node or next_node == node:
                        break
                    
                    node = next_node
                    depth += 1
            
            # ========== 按距离排序 ==========
            if entities:
                player_x, player_y, player_z = entities[0]['x'], entities[0]['y'], entities[0]['z']
                for e in entities:
                    dx = e['x'] - player_x
                    dy = e['y'] - player_y
                    dz = e['z'] - player_z
                    e['distance'] = math.sqrt(dx*dx + dy*dy + dz*dz)
                entities.sort(key=lambda e: e['distance'])
            
            # ========== 显示 ==========
            os.system('cls')
            print("=" * 80)
            print("  🎮 Trove x64 实体读取器 | 按 Ctrl+C 退出")
            print("=" * 80)
            print(f"  玩家坐标: ({player_x:.0f}, {player_y:.0f}, {player_z:.0f})")
            print(f"  发现 {len(entities)} 个怪物 | 按距离从近到远排序")
            print("-" * 80)
            print(f"  {'距离':<6} {'名字':<26} {'血量':<10} {'等级':<5} 坐标")
            print("-" * 80)
            
            for e in entities[:25]:
                if e['health'] >= 1_000_000:
                    hp_str = f"{e['health']/1_000_000:.1f}M"
                else:
                    hp_str = f"{e['health']:.0f}"
                
                print(f"  {e['distance']:.0f}m   {e['name'][:25]:<26} {hp_str:<10} {e['level']:<5} "
                      f"({e['x']:.0f}, {e['y']:.0f}, {e['z']:.0f})")
            
            if len(entities) > 25:
                print(f"\n  ... 还有 {len(entities) - 25} 个怪物")
            print()
            
            time.sleep(REFRESH_RATE)
            
        except KeyboardInterrupt:
            print("\n👋 已退出")
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()

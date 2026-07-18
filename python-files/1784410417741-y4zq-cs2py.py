import pygame
import pymem
import pymem.process
import sys
import time
from ctypes import Structure, c_float, c_int

# ------------------------------------------------------------
# OFFSETS ATUALIZÁVEIS (consulte cs2-dumper)
# https://github.com/a2x/cs2-dumper
# ------------------------------------------------------------
OFFSETS = {
    "dwEntityList": 0x1E019A0,
    "dwLocalPlayerPawn": 0x1AF4A20,
    "m_iHealth": 0x34C,
    "m_iTeamNum": 0x3EB,
    "m_vOldOrigin": 0x15B0,
    "m_sSanitizedPlayerName": 0x778,
    "m_hPlayerPawn": 0x6B4,
}

# ------------------------------------------------------------
# Estrutura de dados (ctypes)
# ------------------------------------------------------------
class Vector3(Structure):
    _fields_ = [("x", c_float), ("y", c_float), ("z", c_float)]

class MemoryReader:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
        except pymem.exception.ProcessNotFound:
            print("[ERRO] CS2 não está rodando!")
            sys.exit(1)
        
        self.client_base = pymem.process.module_from_name(
            self.pm.process_handle, "client.dll"
        ).lpBaseOfDll
        print(f"[OK] client.dll base: 0x{self.client_base:X}")
    
    def read_ptr(self, addr):
        try:
            return self.pm.read_ulonglong(addr)
        except:
            return 0
    
    def read_int(self, addr):
        try:
            return self.pm.read_int(addr)
        except:
            return 0
    
    def read_vec3(self, addr):
        try:
            return self.pm.read_ctype(addr, Vector3)
        except:
            return Vector3(0, 0, 0)
    
    def read_string(self, addr, max_len=32):
        try:
            raw = self.pm.read_bytes(addr, max_len)
            null_idx = raw.find(b'\x00')
            if null_idx != -1:
                raw = raw[:null_idx]
            return raw.decode('utf-8', errors='ignore')
        except:
            return ""

class EntityManager:
    def __init__(self, reader):
        self.reader = reader
        self.entity_list_addr = reader.client_base + OFFSETS["dwEntityList"]
    
    def get_local_player(self):
        local_pawn_addr = self.reader.client_base + OFFSETS["dwLocalPlayerPawn"]
        return self.reader.read_ptr(local_pawn_addr)
    
    def get_players(self):
        players = []
        list_ptr = self.reader.read_ptr(self.entity_list_addr)
        if not list_ptr:
            return players
        
        for i in range(1, 65):
            entry_addr = list_ptr + (8 * (i & 0x7FFF) >> 9) + 16
            controller = self.reader.read_ptr(entry_addr)
            if not controller:
                continue
            
            pawn_handle = self.reader.read_int(controller + OFFSETS["m_hPlayerPawn"])
            if not pawn_handle:
                continue
            
            list_ptr2 = self.reader.read_ptr(self.entity_list_addr + 0x8)
            if not list_ptr2:
                continue
            
            entity_addr = self.reader.read_ptr(
                list_ptr2 + 0x10 * ((pawn_handle & 0x7FFF) >> 9) + 0x10
            )
            if not entity_addr:
                continue
            
            pawn = self.reader.read_ptr(entity_addr + 0x78 * (pawn_handle & 0x1FF))
            if not pawn:
                continue
            
            health = self.reader.read_int(pawn + OFFSETS["m_iHealth"])
            if health <= 0 or health > 100:
                continue
            
            team = self.reader.read_int(pawn + OFFSETS["m_iTeamNum"])
            origin = self.reader.read_vec3(pawn + OFFSETS["m_vOldOrigin"])
            name = self.reader.read_string(pawn + OFFSETS["m_sSanitizedPlayerName"])
            
            players.append({
                "pawn": pawn,
                "health": health,
                "team": team,
                "origin": origin,
                "name": name if name else f"Player_{i}"
            })
        
        return players

# ------------------------------------------------------------
# VISUALIZADOR RADAR (Pygame)
# ------------------------------------------------------------
class RadarViewer:
    def __init__(self, width=800, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Telemetry Radar - Mestrado (Local apenas)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14)
        
        self.BG = (20, 20, 30)
        self.GRID = (60, 60, 80)
        self.COLOR_ALLY = (0, 100, 255)
        self.COLOR_ENEMY = (255, 50, 50)
        self.COLOR_LOCAL = (0, 255, 0)
        self.COLOR_TEXT = (200, 200, 200)
        
        self.scale = 0.08
        self.offset_x = width // 2
        self.offset_y = height // 2
        self.running = True
    
    def world_to_screen(self, world_pos, local_pos):
        dx = (world_pos.x - local_pos.x) * self.scale
        dz = (world_pos.z - local_pos.z) * self.scale
        screen_x = self.offset_x + dz
        screen_y = self.offset_y - dx
        return int(screen_x), int(screen_y)
    
    def draw_grid(self):
        step = 100
        step_px = int(step * self.scale)
        for x in range(-10, 11):
            px = self.offset_x + x * step_px
            if 0 <= px <= self.width:
                pygame.draw.line(self.screen, self.GRID, (px, 0), (px, self.height), 1)
        for y in range(-10, 11):
            py = self.offset_y + y * step_px
            if 0 <= py <= self.height:
                pygame.draw.line(self.screen, self.GRID, (0, py), (self.width, py), 1)
        pygame.draw.line(self.screen, (100, 100, 120), 
                         (self.offset_x - 15, self.offset_y), 
                         (self.offset_x + 15, self.offset_y), 2)
        pygame.draw.line(self.screen, (100, 100, 120), 
                         (self.offset_x, self.offset_y - 15), 
                         (self.offset_x, self.offset_y + 15), 2)
    
    def draw_player(self, pos, local_pos, player_data, is_local=False, is_enemy=True):
        screen_pos = self.world_to_screen(pos, local_pos)
        if screen_pos[0] < -20 or screen_pos[0] > self.width + 20 or \
           screen_pos[1] < -20 or screen_pos[1] > self.height + 20:
            return
        
        color = self.COLOR_LOCAL if is_local else (self.COLOR_ENEMY if is_enemy else self.COLOR_ALLY)
        radius = 8 if is_local else 6
        
        pygame.draw.circle(self.screen, color, screen_pos, radius)
        pygame.draw.circle(self.screen, (255, 255, 255), screen_pos, radius, 1)
        
        name_text = self.font.render(player_data["name"], True, self.COLOR_TEXT)
        self.screen.blit(name_text, (screen_pos[0] - 20, screen_pos[1] - 25))
        health_text = self.font.render(f"{player_data['health']}HP", True, (200, 200, 200))
        self.screen.blit(health_text, (screen_pos[0] - 15, screen_pos[1] + 10))
    
    def draw_info(self, local_player, total_players, fps):
        y = 10
        lines = [
            f"FPS: {fps:.1f}",
            f"Jogadores: {total_players}",
            f"Local: {local_player['name'] if local_player else 'N/A'}",
            "VERDE=VC | AZUL=ALIADO | VERMELHO=INIMIGO"
        ]
        for line in lines:
            text = self.font.render(line, True, self.COLOR_TEXT)
            self.screen.blit(text, (10, y))
            y += 22
    
    def run(self, reader, entity_manager):
        local_pawn = entity_manager.get_local_player()
        local_data = None
        players = entity_manager.get_players()
        for p in players:
            if p["pawn"] == local_pawn:
                local_data = p
                break
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            players = entity_manager.get_players()
            local_pawn = entity_manager.get_local_player()
            local_data = None
            for p in players:
                if p["pawn"] == local_pawn:
                    local_data = p
                    break
            if not local_data and players:
                local_data = players[0]
            
            self.screen.fill(self.BG)
            self.draw_grid()
            
            if local_data:
                for player in players:
                    is_local = (player["pawn"] == local_pawn)
                    is_enemy = (player["team"] != local_data["team"]) if local_data else False
                    self.draw_player(player["origin"], local_data["origin"], player,
                                     is_local=is_local, is_enemy=is_enemy)
            
            self.draw_info(local_data, len(players), self.clock.get_fps())
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    print("=" * 50)
    print("RADAR TELEMETRIA - PROJETO DE MESTRADO")
    print("USO EXCLUSIVO PARA TESTES LOCALS (-insecure)")
    print("=" * 50)
    reader = MemoryReader()
    entity_manager = EntityManager(reader)
    radar = RadarViewer()
    try:
        radar.run(reader, entity_manager)
    except KeyboardInterrupt:
        print("\n[OK] Radar encerrado.")
    except Exception as e:
        print(f"[ERRO] {e}")

if __name__ == "__main__":
    main()
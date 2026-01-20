import pygame
import sys
import random
import math
from pygame import mixer

# Initialize pygame
pygame.init()
mixer.init()

# Screen dimensions
SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 800
REEL_WIDTH = 200
REEL_HEIGHT = 350
SYMBOL_SIZE = 150

# Colors
BACKGROUND_COLOR = (20, 50, 90)
PANEL_COLOR = (30, 60, 110)
REEL_BG_COLOR = (10, 30, 60)
TEXT_COLOR = (255, 255, 255)
BALANCE_COLOR = (100, 255, 100)
BET_COLOR = (255, 220, 100)
BUTTON_COLOR = (200, 60, 60)
BUTTON_HOVER_COLOR = (230, 80, 80)
WIN_COLOR = (255, 215, 0)
INFO_BUTTON_COLOR = (60, 150, 200)
INFO_BUTTON_HOVER_COLOR = (80, 170, 220)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PyGame Slot Machine - 3 Reels")

# Fonts
title_font = pygame.font.SysFont('arial', 48, bold=True)
font = pygame.font.SysFont('arial', 28)
small_font = pygame.font.SysFont('arial', 24)
button_font = pygame.font.SysFont('arial', 22)
symbol_font = pygame.font.SysFont('arial', 32, bold=True)

# Game variables
balance = 1000
current_bet = 10
winnings = 0
reel_states = [0, 0, 0]  # Which symbol is at the top of each reel (3 reels only)
reel_spinning = [False, False, False]
spin_speed = [0, 0, 0]
win_animation = 0
win_amount = 0
game_state = "ready"  # "ready", "spinning", "results"
show_payouts = False  # Whether to show the payout table
spin_count = 0  # Track spins

# Create symbols with colors and names - Simple classic slot symbols
symbols = [
    {"name": "7", "color": (255, 50, 50), "payout": 100, "payout_2": 10},
    {"name": "BAR", "color": (255, 255, 100), "payout": 50, "payout_2": 5},
    {"name": "BELL", "color": (255, 150, 50), "payout": 30, "payout_2": 3},
    {"name": "DIAMOND", "color": (100, 200, 255), "payout": 20, "payout_2": 2},
    {"name": "CHERRY", "color": (255, 50, 100), "payout": 15, "payout_2": 2},
    {"name": "LEMON", "color": (255, 255, 100), "payout": 10, "payout_2": 1},
]

# Button definitions
class Button:
    def __init__(self, x, y, width, height, text, action, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hover = False
        self.color = color if color else BUTTON_COLOR
        self.hover_color = hover_color if hover_color else BUTTON_HOVER_COLOR
        
    def draw(self):
        color = self.hover_color if self.hover else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=8)
        
        # Use button font for better fitting
        text_surf = button_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action
        return None

# Create buttons - Cleaner layout
buttons = [
    # Bet controls (top row)
    Button(50, 600, 140, 50, "BET -10", "bet_down"),
    Button(200, 600, 140, 50, "BET +10", "bet_up"),
    Button(350, 600, 140, 50, "MIN BET", "min_bet"),
    Button(500, 600, 140, 50, "MAX BET", "max_bet"),
    
    # Main action buttons (middle row)
    Button(650, 600, 140, 50, "SPIN", "spin"),
    Button(800, 600, 140, 50, "AUTO SPIN", "auto_spin"),
    
    # Info and control buttons (bottom row)
    Button(950, 600, 140, 50, "PAYOUTS", "show_payouts", INFO_BUTTON_COLOR, INFO_BUTTON_HOVER_COLOR),
    Button(1100, 600, 140, 50, "RESET", "reset"),
    
    # Cash out and quit (at the bottom)
    Button(50, 670, 140, 50, "CASH OUT", "cash_out"),
    Button(1100, 670, 140, 50, "QUIT", "quit"),
]

# Function to draw a symbol
def draw_symbol(symbol_idx, x, y, size, highlight=False):
    symbol = symbols[symbol_idx]
    
    # Draw symbol background
    symbol_rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, symbol["color"], symbol_rect, border_radius=15)
    
    # Add highlight effect for wins
    if highlight:
        pygame.draw.rect(screen, (255, 255, 255, 150), symbol_rect, 4, border_radius=15)
    
    # Draw symbol border
    pygame.draw.rect(screen, (255, 255, 255), symbol_rect, 3, border_radius=15)
    
    # Draw symbol name (big and centered)
    name_surf = symbol_font.render(symbol["name"], True, TEXT_COLOR)
    name_rect = name_surf.get_rect(center=(x + size//2, y + size//2))
    screen.blit(name_surf, name_rect)
    
    # Draw payout in corner
    payout_font = pygame.font.SysFont('arial', 20)
    payout_surf = payout_font.render(f"x{symbol['payout']}", True, (255, 255, 200))
    payout_rect = payout_surf.get_rect(bottomright=(x + size - 10, y + size - 10))
    screen.blit(payout_surf, payout_rect)

# Function to draw the reels (3x1 layout) - MOVED LOWER
def draw_reels():
    reel_start_x = (SCREEN_WIDTH - (3 * REEL_WIDTH + 2 * 50)) // 2
    reel_start_y = 220  # MOVED LOWER (was 180)
    
    # Draw reel backgrounds
    for i in range(3):  # Only 3 reels
        reel_x = reel_start_x + i * (REEL_WIDTH + 50)
        reel_rect = pygame.Rect(reel_x, reel_start_y, REEL_WIDTH, REEL_HEIGHT)
        pygame.draw.rect(screen, REEL_BG_COLOR, reel_rect, border_radius=15)
        pygame.draw.rect(screen, (50, 100, 180), reel_rect, 4, border_radius=15)
        
        # Draw only the center symbol (single visible symbol per reel)
        symbol_pos = reel_states[i] % len(symbols)
        symbol_y = reel_start_y + (REEL_HEIGHT // 2 - SYMBOL_SIZE // 2)
        
        # Highlight if part of a win
        highlight = False
        if win_animation > 0 and win_amount > 0:
            # Check if this reel is part of the winning combination
            highlight = True
        
        draw_symbol(symbol_pos, reel_x + (REEL_WIDTH - SYMBOL_SIZE) // 2, 
                   symbol_y, SYMBOL_SIZE, highlight)
    
    # Draw connecting line between reels
    line_y = reel_start_y + REEL_HEIGHT // 2
    line_start_x = reel_start_x + REEL_WIDTH // 2
    line_end_x = reel_start_x + 2 * (REEL_WIDTH + 50) + REEL_WIDTH // 2
    
    if win_animation > 0:
        # Animated winning line
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 100 + 50
        line_color = (255, 255, 100, int(pulse))
        line_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(line_surface, line_color, (line_start_x, line_y), (line_end_x, line_y), 8)
        screen.blit(line_surface, (0, 0))

# Function to draw payout table overlay
def draw_payout_table():
    # Create semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))  # Black with transparency
    screen.blit(overlay, (0, 0))
    
    # Draw payout table panel
    table_width = 600
    table_height = 500
    table_x = (SCREEN_WIDTH - table_width) // 2
    table_y = (SCREEN_HEIGHT - table_height) // 2
    
    table_rect = pygame.Rect(table_x, table_y, table_width, table_height)
    pygame.draw.rect(screen, PANEL_COLOR, table_rect, border_radius=15)
    pygame.draw.rect(screen, (100, 150, 255), table_rect, 4, border_radius=15)
    
    # Draw title
    title = title_font.render("PAYOUT TABLE", True, WIN_COLOR)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, table_y + 30))
    
    # Draw header
    header_font = pygame.font.SysFont('arial', 32, bold=True)
    headers = ["SYMBOL", "3 MATCH", "2 MATCH", "COLOR"]
    header_y = table_y + 100
    
    for i, header in enumerate(headers):
        header_text = header_font.render(header, True, (255, 255, 200))
        screen.blit(header_text, (table_x + 50 + i * 150, header_y))
    
    # Draw separator line
    pygame.draw.line(screen, (100, 150, 255), 
                    (table_x + 40, header_y + 40), 
                    (table_x + table_width - 40, header_y + 40), 2)
    
    # Draw symbol payouts
    symbol_y = header_y + 70
    
    for i, symbol in enumerate(symbols):
        # Draw symbol color box
        color_box = pygame.Rect(table_x + 50, symbol_y, 40, 40)
        pygame.draw.rect(screen, symbol["color"], color_box, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), color_box, 2, border_radius=8)
        
        # Draw symbol name
        name_text = font.render(symbol["name"], True, TEXT_COLOR)
        screen.blit(name_text, (table_x + 100, symbol_y + 5))
        
        # Draw 3-match payout
        payout_3_text = font.render(f"x{symbol['payout']}", True, WIN_COLOR)
        screen.blit(payout_3_text, (table_x + 200, symbol_y + 5))
        
        # Draw 2-match payout
        payout_2_text = font.render(f"x{symbol['payout_2']}", True, (255, 200, 100))
        screen.blit(payout_2_text, (table_x + 350, symbol_y + 5))
        
        # Draw color preview
        color_preview = pygame.Rect(table_x + 500, symbol_y, 40, 40)
        pygame.draw.rect(screen, symbol["color"], color_preview, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), color_preview, 2, border_radius=8)
        
        symbol_y += 60
    
    # Draw game rules at the bottom
    rules = [
        "• Match 3 of the same symbol = Win full payout",
        "• Match 2 of the same symbol = Win reduced payout",
        "• No match = No win",
        "• Minimum bet: $10, Maximum bet: $100"
    ]
    
    rules_y = table_y + table_height - 150
    for i, rule in enumerate(rules):
        rule_text = small_font.render(rule, True, (200, 230, 255))
        screen.blit(rule_text, (table_x + 50, rules_y + i * 30))
    
    # Draw close button
    close_button = Button(SCREEN_WIDTH // 2 - 70, table_y + table_height - 50, 140, 40, 
                         "CLOSE", "close_payouts", INFO_BUTTON_COLOR, INFO_BUTTON_HOVER_COLOR)
    close_button.check_hover(pygame.mouse.get_pos())
    close_button.draw()
    
    return close_button

# Function to draw the game interface
def draw_interface():
    # Draw background
    screen.fill(BACKGROUND_COLOR)
    
    # Draw decorative border
    pygame.draw.rect(screen, (50, 100, 180), (20, 20, SCREEN_WIDTH-40, SCREEN_HEIGHT-40), 4, border_radius=10)
    
    # Draw title
    title_surf = title_font.render("CLASSIC 3-REEL SLOT MACHINE", True, (255, 255, 200))
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
    screen.blit(title_surf, title_rect)
    
    # Draw balance panel
    balance_panel = pygame.Rect(50, 120, 300, 80)
    pygame.draw.rect(screen, PANEL_COLOR, balance_panel, border_radius=10)
    pygame.draw.rect(screen, (100, 150, 255), balance_panel, 3, border_radius=10)
    
    balance_text = font.render(f"BALANCE: ${balance:,.2f}", True, BALANCE_COLOR)
    screen.blit(balance_text, (balance_panel.x + 20, balance_panel.y + 25))
    
    # Draw current bet panel
    bet_panel = pygame.Rect(SCREEN_WIDTH - 350, 120, 300, 80)
    pygame.draw.rect(screen, PANEL_COLOR, bet_panel, border_radius=10)
    pygame.draw.rect(screen, (100, 150, 255), bet_panel, 3, border_radius=10)
    
    bet_text = font.render(f"BET: ${current_bet:,.2f}", True, BET_COLOR)
    screen.blit(bet_text, (bet_panel.x + 20, bet_panel.y + 25))
    
    # Draw winnings panel
    winnings_panel = pygame.Rect(SCREEN_WIDTH // 2 - 150, 120, 300, 80)
    pygame.draw.rect(screen, PANEL_COLOR, winnings_panel, border_radius=10)
    pygame.draw.rect(screen, (100, 150, 255), winnings_panel, 3, border_radius=10)
    
    winnings_color = WIN_COLOR if winnings > 0 else TEXT_COLOR
    winnings_text = font.render(f"WINNINGS: ${winnings:,.2f}", True, winnings_color)
    screen.blit(winnings_text, (winnings_panel.x + 20, winnings_panel.y + 25))
    
    # Draw reels (3x1 layout) - NOW LOWER
    draw_reels()
    
    # Draw spin counter
    spin_text = small_font.render(f"SPINS: {spin_count}", True, (200, 230, 255))
    screen.blit(spin_text, (SCREEN_WIDTH - 150, 260))
    
    # Draw buttons
    for button in buttons:
        button.draw()
    
    # Draw game state message
    if game_state == "spinning":
        state_text = font.render("SPINNING...", True, (255, 200, 100))
    elif game_state == "results":
        if win_amount > 0:
            state_text = font.render(f"YOU WON ${win_amount:,.2f}!", True, WIN_COLOR)
        else:
            state_text = font.render("NO WIN THIS TIME", True, (255, 100, 100))
    else:
        state_text = font.render("READY TO SPIN", True, (100, 255, 100))
    
    state_rect = state_text.get_rect(center=(SCREEN_WIDTH // 2, 720))
    screen.blit(state_text, state_rect)
    
    # Draw quick game info
    info_text = small_font.render("Press PAYOUTS button to see win table", True, (200, 230, 255))
    screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, 760))
    
    # Draw payout table if button is pressed
    close_button = None
    if show_payouts:
        close_button = draw_payout_table()
    
    return close_button

# Function to start spinning - COMPLETELY FIXED
def start_spin():
    global game_state, balance, current_bet, reel_spinning, spin_speed, win_animation, spin_count, win_amount
    
    if balance < current_bet:
        return  # Not enough money to spin
    
    # Check if we can spin (only if ready or showing results)
    if game_state != "ready" and game_state != "results":
        return  # Already spinning
    
    # Reset win amount for new spin
    win_amount = 0
    
    # Deduct bet from balance
    balance -= current_bet
    
    # Reset win animation
    win_animation = 0
    
    # Set all reels to spinning
    for i in range(3):
        reel_spinning[i] = True
        spin_speed[i] = random.randint(20, 30)  # Random starting speed
    
    # Set game state to spinning
    game_state = "spinning"
    spin_count += 1

# Function to stop spinning and calculate results - FIXED
def stop_spin():
    global game_state, reel_spinning, win_amount, winnings, balance, win_animation
    
    # Get random final positions for each reel
    spin_symbols = []
    for i in range(3):
        reel_states[i] = random.randint(0, len(symbols) - 1)
        spin_symbols.append(reel_states[i])
    
    # Check for wins
    win_multiplier = 0
    
    # Count how many of each symbol we have
    symbol_counts = {}
    for symbol_idx in spin_symbols:
        symbol_counts[symbol_idx] = symbol_counts.get(symbol_idx, 0) + 1
    
    # Check for 3 of a kind
    for symbol_idx, count in symbol_counts.items():
        if count == 3:  # 3 matching symbols
            win_multiplier = symbols[symbol_idx]["payout"]
            break
    
    # Check for 2 of a kind
    if win_multiplier == 0:
        for symbol_idx, count in symbol_counts.items():
            if count == 2:  # 2 matching symbols
                win_multiplier = symbols[symbol_idx]["payout_2"]
                break
    
    # Calculate win amount
    win_amount = current_bet * win_multiplier
    
    if win_amount > 0:
        winnings += win_amount
        balance += win_amount
        win_animation = 100  # Start win animation
    
    # IMPORTANT: Set game state to results
    game_state = "results"

# Function to update spinning reels - FIXED
def update_spin():
    global reel_states, reel_spinning, game_state
    
    # Check if all reels have stopped
    all_stopped = True
    
    # Update each spinning reel
    for i in range(3):
        if reel_spinning[i]:
            # Move reel forward
            reel_states[i] = (reel_states[i] + 1) % len(symbols)
            spin_speed[i] -= 0.8  # Slow down over time
            
            if spin_speed[i] <= 0:
                reel_spinning[i] = False
            else:
                all_stopped = False
    
    # If all reels stopped, calculate results
    if all_stopped:
        stop_spin()

# Function to reset game state after win animation - NEW FUNCTION
def reset_for_next_spin():
    global game_state, win_animation
    
    # If we're in results state and win animation is done, go back to ready
    if game_state == "results" and win_animation <= 0:
        game_state = "ready"

# Function to update win animation
def update_animation():
    global win_animation
    
    if win_animation > 0:
        win_animation -= 2  # Faster animation

# Function to handle auto spin
auto_spin_active = False
auto_spin_count = 0
auto_spin_delay = 0  # Add delay between auto spins

def toggle_auto_spin():
    global auto_spin_active, auto_spin_count
    
    if auto_spin_active:
        auto_spin_active = False
        auto_spin_count = 0
    else:
        auto_spin_active = True
        auto_spin_count = 10  # Do 10 auto spins

# Reset game function
def reset_game():
    global balance, current_bet, winnings, win_amount, game_state, win_animation, spin_count
    balance = 1000
    current_bet = 10
    winnings = 0
    win_amount = 0
    game_state = "ready"
    win_animation = 0
    spin_count = 0
    # Reset reels
    for i in range(3):
        reel_spinning[i] = False
        reel_states[i] = 0

# Main game loop
clock = pygame.time.Clock()
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle button clicks
        if not show_payouts:
            for button in buttons:
                action = button.handle_event(event)
                if action:
                    if action == "spin":
                        start_spin()
                    elif action == "max_bet":
                        current_bet = min(100, balance)
                    elif action == "min_bet":
                        current_bet = 10
                    elif action == "auto_spin":
                        toggle_auto_spin()
                    elif action == "bet_down":
                        current_bet = max(10, current_bet - 10)
                    elif action == "bet_up":
                        current_bet = min(balance, current_bet + 10)
                    elif action == "show_payouts":
                        show_payouts = True
                    elif action == "cash_out":
                        print(f"Cashing out! Final balance: ${balance:,.2f}")
                        running = False
                    elif action == "reset":
                        reset_game()
                    elif action == "quit":
                        running = False
        else:
            # Handle clicks on payout table
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if click is outside the payout table
                table_width = 600
                table_height = 500
                table_x = (SCREEN_WIDTH - table_width) // 2
                table_y = (SCREEN_HEIGHT - table_height) // 2
                
                click_rect = pygame.Rect(table_x, table_y, table_width, table_height)
                if not click_rect.collidepoint(event.pos):
                    show_payouts = False
        
        # Handle keyboard input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and (game_state == "ready" or game_state == "results"):
                start_spin()
            elif event.key == pygame.K_UP:
                current_bet = min(balance, current_bet + 10)
            elif event.key == pygame.K_DOWN:
                current_bet = max(10, current_bet - 10)
            elif event.key == pygame.K_m:
                current_bet = min(100, balance)
            elif event.key == pygame.K_a:
                toggle_auto_spin()
            elif event.key == pygame.K_p:
                show_payouts = not show_payouts
            elif event.key == pygame.K_ESCAPE:
                if show_payouts:
                    show_payouts = False
                else:
                    running = False
            elif event.key == pygame.K_r:
                reset_game()
            elif event.key == pygame.K_1:
                current_bet = 10
            elif event.key == pygame.K_2:
                current_bet = 25
            elif event.key == pygame.K_3:
                current_bet = 50
            elif event.key == pygame.K_4:
                current_bet = 100
    
    # Update button hover states (only if not showing payouts)
    if not show_payouts:
        for button in buttons:
            button.check_hover(mouse_pos)
    
    # Handle auto spin
    if auto_spin_active and (game_state == "ready" or game_state == "results"):
        # Small delay between auto spins
        if auto_spin_delay <= 0:
            if auto_spin_count > 0:
                start_spin()
                auto_spin_count -= 1
                auto_spin_delay = 30  # 1 second delay at 30 FPS
            else:
                auto_spin_active = False
        else:
            auto_spin_delay -= 1
    
    # Update game state
    if game_state == "spinning":
        update_spin()
    
    # Update animations
    update_animation()
    
    # Check if we should reset for next spin
    reset_for_next_spin()
    
    # Draw everything
    draw_interface()
    
    # Update display
    pygame.display.flip()
    
    # Control frame rate
    clock.tick(30)

# Quit pygame
pygame.quit()
sys.exit()
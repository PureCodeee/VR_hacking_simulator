"""
Hacknet Simulator
Interactive ethical hacking training simulator

Controls:
- Type commands into the terminal
- Press ENTER to execute

Example commands:
help
scan
status
attack ddos
attack bruteforce
attack phishing
attack sqli
firewall on
firewall off
ids on
ids off
reset
"""

import math
import random
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

try:
    import pygame
except ImportError:
    print("This project requires pygame. Install it with: pip install pygame")
    sys.exit(1)


WIDTH, HEIGHT = 1580, 720
FPS = 60
MAP_X = 980
MAP_Y = 80
MAP_WIDTH = 560
MAP_HEIGHT = 600
BG = (10, 14, 24)
PANEL = (18, 24, 38)
PANEL_2 = (22, 30, 48)
GRID = (28, 36, 58)
TEXT = (225, 232, 245)
MUTED = (140, 152, 176)
GREEN = (80, 220, 140)
YELLOW = (255, 208, 102)
RED = (255, 92, 92)
BLUE = (86, 156, 255)
CYAN = (94, 235, 255)
PURPLE = (181, 116, 255)
ORANGE = (255, 165, 80)
WHITE = (245, 247, 252)


@dataclass
class Node:
    name: str
    x: int
    y: int
    kind: str
    status: str = "normal"  # normal / warning / compromised / protected
    hp: int = 100
    max_hp: int = 100

    def color(self):
        if self.status == "compromised":
            return RED
        if self.status == "warning":
            return YELLOW
        if self.status == "protected":
            return GREEN
        return BLUE


@dataclass
class Packet:
    start: Tuple[float, float]
    end: Tuple[float, float]
    kind: str
    progress: float = 0.0
    speed: float = 0.6
    color: Tuple[int, int, int] = CYAN
    damage: int = 0
    target: Optional[str] = None
    attack_name: str = ""

    def update(self, dt: float):
        self.progress += self.speed * dt

    def position(self):
        sx, sy = self.start
        ex, ey = self.end
        t = max(0.0, min(1.0, self.progress))
        x = sx + (ex - sx) * t
        y = sy + (ey - sy) * t
        return x, y

    def done(self) -> bool:
        return self.progress >= 1.0


@dataclass
class Attack:
    name: str
    severity: int
    interval: float
    duration: float
    target_node: str

    timer: float = 0.0
    elapsed: float = 0.0

    active: bool = False
    finished: bool = False

    color: Tuple[int, int, int] = RED


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    action: str
    active: bool = False


class Terminal:
    def __init__(self):
        self.input_text = ""
        self.history = []
        

    def add_line(self, text: str):
        self.history.append(text)
        self.history = self.history[-22:]


class HacknetSimulator:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Hacknet Simulator")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 16)
        self.font_big = pygame.font.SysFont("consolas", 30, bold=True)
        self.font_terminal = pygame.font.SysFont("consolas", 15)
        self.font_huge = pygame.font.SysFont("consolas", 42, bold=True)

        self.nodes = self._create_nodes()
        self.links = self._create_links()
        self.packets: List[Packet] = []
        self.attacks = self._create_attacks()
        self.buttons = []
        self.terminal = Terminal()
        self.terminal.add_line("HACKNET OS v1.0")
        self.terminal.add_line("Educational Ethical Hacking Environment")
        self.terminal.add_line("Type 'help' for available commands")
        self.logs = self.terminal.history
        self.overall_threat = 12
        self.network_integrity = 100
        self.selected_attack: Optional[str] = None
        self.sim_time = 0.0
        self.packet_spawn_timer = 0.0
        self.auto_attack = False
        self.running = True
        self.firewall_enabled = True
        self.ids_enabled = True
        self.defense_bonus = 0
        self.day_tick = 0.0
        self.critical_alert_shown = False

    def _create_nodes(self) -> List[Node]:
        return [
            Node("Client", 180, 160, "endpoint"),
            Node("Gateway", 380, 180, "router"),
            Node("Firewall", 580, 160, "defense", status="protected"),
            Node("Web Server", 780, 220, "server"),
            Node("Database", 950, 350, "database"),
            Node("Admin Panel", 720, 470, "service"),
            Node("Security Console", 460, 420, "monitor", status="protected"),
        ]

    def _create_links(self):
        return [
            ("Client", "Gateway"),
            ("Gateway", "Firewall"),
            ("Firewall", "Web Server"),
            ("Web Server", "Database"),
            ("Firewall", "Admin Panel"),
            ("Gateway", "Security Console"),
            ("Security Console", "Firewall"),
        ]

    def _create_attacks(self) -> List[Attack]:
        return [
            Attack(
                "DDoS",
                severity=22,
                interval=0.15,
                duration=15,
                target_node="Web Server",
                color=RED
            ),

            Attack(
                "Brute Force",
                severity=14,
                interval=0.35,
                duration=12,
                target_node="Admin Panel",
                color=ORANGE
            ),

            Attack(
                "Phishing",
                severity=10,
                interval=0.90,
                duration=10,
                target_node="Admin Panel",
                color=PURPLE
            ),

            Attack(
                "SQL Injection",
                severity=16,
                interval=0.45,
                duration=14,
                target_node="Database",
                color=CYAN
            ),
        ]

    def _create_buttons(self):
        return []

    def log(self, message: str):
        timestamp = pygame.time.get_ticks() // 1000
        formatted = f"[{timestamp:04d}s] {message}"
        self.terminal.add_line(formatted)
        self.logs = self.terminal.history

    def node_by_name(self, name: str) -> Node:
        for node in self.nodes:
            if node.name == name:
                return node
        raise KeyError(name)

    def link_positions(self, a: str, b: str):
        na = self.node_by_name(a)
        nb = self.node_by_name(b)
        return (na.x, na.y), (nb.x, nb.y)

    def spawn_packet(
        self,
        kind,
        start_name,
        end_name,
        damage,
        color,
        attack_name,
        speed=0.55
    ):        
        start_node = self.node_by_name(start_name)
        end_node = self.node_by_name(end_name)
        packet = Packet(
            start=(start_node.x, start_node.y),
            end=(end_node.x, end_node.y),
            kind=kind,
            speed=speed,
            color=color,
            damage=damage,
            target=end_name,
            attack_name=attack_name,
        )
        
        self.packets.append(packet)

    def apply_attack_effect(self, attack_name: str):
        if attack_name == "DDoS":
            self.overall_threat += 10
            self.log("[WARNING] Massive DDoS traffic flood detected.")
        elif attack_name == "Brute Force":
            self.overall_threat += 6
            self.log("[WARNING] Multiple unauthorized login attempts detected.")
        elif attack_name == "Phishing":
            self.overall_threat += 5
            self.log("[ALERT] Suspicious phishing payload delivered.")
        elif attack_name == "SQL Injection":
            self.overall_threat += 8
            self.log("[WARNING] SQL injection signature identified.")
        self.overall_threat = min(100, self.overall_threat)

    def launch_attack(self, attack_name: str, duration=None):

        if self.auto_attack:
            self.log("Another attack is already running.")
            return

        self.selected_attack = attack_name
        self.auto_attack = True

        for attack in self.attacks:

            attack.active = attack.name == attack_name
            attack.timer = 0.0
            attack.elapsed = 0.0
            attack.finished = False

            if attack.active:

                if duration:
                    attack.duration = duration

                self.log(f"[SCENARIO] Launching {attack.name} attack simulation.")
                self.log(f"[TARGET] {attack.target_node}")
                self.log(f"[DURATION] {int(attack.duration)} seconds")

    def reset_system(self):
        self.critical_alert_shown = False
        for node in self.nodes:
            node.status = "normal" if node.kind not in {"defense", "monitor"} else "protected"
            node.hp = node.max_hp
        self.packets.clear()
        self.overall_threat = 12
        self.network_integrity = 100
        self.selected_attack = None
        self.auto_attack = False
        for attack in self.attacks:
            attack.active = False
            attack.timer = 0.0
        self.firewall_enabled = True
        self.ids_enabled = True
        self.log("[SYS] Full network reset completed.")

    def toggle_firewall(self):
        self.firewall_enabled = not self.firewall_enabled
        firewall = self.node_by_name("Firewall")
        firewall.status = "protected" if self.firewall_enabled else "normal"
        self.log(f"[DEFENSE] Firewall {'ONLINE' if self.firewall_enabled else 'OFFLINE'}.")

    def toggle_ids(self):
        self.ids_enabled = not self.ids_enabled
        console = self.node_by_name("Security Console")
        console.status = "protected" if self.ids_enabled else "normal"
        self.log(f"[DEFENSE] IDS {'ONLINE' if self.ids_enabled else 'OFFLINE'}.")

    def clear_logs(self):
        self.terminal.history.clear()
        self.logs = self.terminal.history
        self.log("[SYS] Terminal buffer cleared.")

    def handle_button(self, action: str):
        pass

    def adjust_damage(self, attack_name: str, base_damage: int) -> int:
        damage = base_damage
        if self.firewall_enabled and attack_name in {"DDoS", "SQL Injection"}:
            damage = int(damage * 0.55)
        if self.ids_enabled and attack_name in {"Brute Force", "Phishing"}:
            damage = int(damage * 0.65)
        return max(1, damage)

    def update_nodes_from_threat(self):
        for node in self.nodes:
            if node.name in {"Firewall", "Security Console"}:
                continue
            if self.overall_threat >= 70 and node.status == "normal":
                node.status = "warning"
            if self.overall_threat >= 90:
                node.status = "compromised" if node.kind in {"server", "database", "service"} else node.status

    def update(self, dt: float):
        self.sim_time += dt
        self.day_tick += dt

        if self.auto_attack and self.selected_attack:
            selected = next((a for a in self.attacks if a.name == self.selected_attack), None)
            if selected:
                selected.timer += dt
                selected.elapsed += dt

                if selected.timer >= selected.interval:
                    selected.timer = 0.0
                    self._auto_generate(selected)

                if selected.elapsed >= selected.duration:
                    self.finish_attack(selected)

        for packet in list(self.packets):
            packet.update(dt)
            if packet.done():
                self.resolve_packet(packet)
                self.packets.remove(packet)

        if self.day_tick >= 1.0:
            self.day_tick = 0.0
            self.overall_threat = max(0, self.overall_threat - (1 if self.ids_enabled else 0))
            self.update_nodes_from_threat()

        if self.overall_threat >= 100:

            self.overall_threat = 100

            if not self.critical_alert_shown:

                self.log("[CRITICAL] Threat level reached maximum.")

                self.critical_alert_shown = True


    def finish_attack(self, attack):

        self.critical_alert_shown = False

        self.auto_attack = False

        target = self.node_by_name(attack.target_node)

        success = False

        if target.status == "compromised":
            success = True

        if self.network_integrity <= 35:
            success = True

        self.log("--------------------------------")

        if success:
            self.log(f"[CRITICAL] {attack.name} attack SUCCESSFUL.")
            self.log(f"[RESULT] Target {target.name} compromised.")
        else:
            self.log(f"[DEFENSE] {attack.name} attack BLOCKED.")
            self.log("[RESULT] Defensive systems held.")

        self.log("--------------------------------")

        self.selected_attack = None

        self.packets.clear()

        for a in self.attacks:
            a.active = False
            a.finished = False
            a.elapsed = 0
            a.timer = 0


    def _auto_generate(self, attack: Attack):
        if attack.name == "DDoS":
            targets = ["Firewall", "Web Server", "Gateway"]
            target = random.choice(targets)
            self.spawn_packet("ddos", "Client", target, attack.severity, attack.color, attack.name, speed=random.uniform(0.7, 1.1))
            self.apply_attack_effect(attack.name)
        elif attack.name == "Brute Force":
            self.spawn_packet("login", "Client", "Admin Panel", attack.severity, attack.color, attack.name, speed=0.55)
            self.apply_attack_effect(attack.name)
        elif attack.name == "Phishing":
            self.spawn_packet("email", "Client", "Admin Panel", attack.severity, attack.color, attack.name, speed=0.42)
            self.apply_attack_effect(attack.name)
        elif attack.name == "SQL Injection":
            self.spawn_packet("query", "Gateway", "Database", attack.severity, attack.color, attack.name, speed=0.60)
            self.apply_attack_effect(attack.name)

    def resolve_packet(self, packet: Packet):
        target = self.node_by_name(packet.target) if packet.target else None
        if not target:
            return

        damage = self.adjust_damage(
            packet.attack_name,
            packet.damage
        )        
        if target.name == "Firewall" and self.firewall_enabled:
            target.status = "protected"
            self.log("[BLOCKED] Firewall intercepted malicious traffic.")
            self.overall_threat = max(0, self.overall_threat - 2)
            return

        if target.name == "Security Console" and self.ids_enabled:
            self.log("[DETECTED] IDS flagged suspicious network activity.")
            self.overall_threat = max(0, self.overall_threat - 2)
            return

        if target.name == "Database" and packet.kind == "query":
            target.status = "warning"
            target.hp = max(0, target.hp - damage)
            self.overall_threat += 4
            self.log(f"[CRITICAL] Database integrity reduced by {damage}%.")
            self.network_integrity = max(0, self.network_integrity - damage)
        elif target.name == "Admin Panel" and packet.kind in {"login", "email"}:
            target.status = "warning"
            target.hp = max(0, target.hp - damage)
            self.overall_threat += 3
            self.log(f"[WARNING] Admin panel compromised attempt: -{damage}% integrity.")
            self.network_integrity = max(0, self.network_integrity - damage)
        elif target.name == "Web Server" and packet.kind == "ddos":
            target.status = "warning"
            target.hp = max(0, target.hp - damage)
            self.overall_threat += 5
            self.log(f"[ALERT] Web server overloaded by DDoS attack.")
            self.network_integrity = max(0, self.network_integrity - damage)
        elif target.name == "Gateway" and packet.kind == "ddos":
            target.status = "warning"
            target.hp = max(0, target.hp - damage)
            self.overall_threat += 2
            self.log(f"[WARNING] Gateway traffic spike detected.")
            self.network_integrity = max(0, self.network_integrity - damage)
        else:
            target.status = "warning"
            target.hp = max(0, target.hp - max(1, damage // 2))
            self.log(f"Packet processed by {target.name}.")

        if target.hp <= 35 and target.status != "compromised":
            target.status = "compromised"
            self.log(f"[CRITICAL] {target.name} node fully compromised.")
            self.overall_threat += 10

        self.overall_threat = min(100, self.overall_threat)
        self.update_nodes_from_threat()

    def draw_grid(self):
        for x in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(self.screen, GRID, (0, y), (WIDTH, y), 1)

    def draw_links(self):
        map_rect = pygame.Rect(MAP_X, MAP_Y, MAP_WIDTH, MAP_HEIGHT)
        pygame.draw.rect(self.screen, (8, 18, 30), map_rect)
        pygame.draw.rect(self.screen, CYAN, map_rect, 2)

        title = self.font_small.render("NETWORK MAP", True, CYAN)
        self.screen.blit(title, (MAP_X + MAP_WIDTH / 2 - 50, MAP_Y + 15))

        for a, b in self.links:
            na = self.node_by_name(a)
            nb = self.node_by_name(b)
            col = CYAN
            if na.status == "warning" or nb.status == "warning":
                col = YELLOW
            if na.status == "compromised" or nb.status == "compromised":
                col = RED

            ax = MAP_X + na.x * 0.45
            ay = MAP_Y + na.y * 0.45

            bx = MAP_X + nb.x * 0.45
            by = MAP_Y + nb.y * 0.45

            pygame.draw.line(
                self.screen,
                col,
                (ax, ay),
                (bx, by),
                2
            )
        

    def draw_nodes(self):
        for node in self.nodes:
            draw_x = MAP_X + node.x * 0.45
            draw_y = MAP_Y + node.y * 0.45

            color = GREEN
            if node.status == "warning":
                color = YELLOW
            elif node.status == "compromised":
                color = RED
            elif node.status == "protected":
                color = CYAN

            pygame.draw.rect(self.screen, color, (draw_x - 25, draw_y - 15, 50, 30), 2)
            pygame.draw.circle(self.screen, color, (draw_x, draw_y), 3)

            label = self.font_small.render(node.name.upper(), True, color)
            self.screen.blit(label, (draw_x - 30, draw_y - 32))

    def draw_packets(self):
        for packet in self.packets:
            x, y = packet.position()
            x = MAP_X + x * 0.45
            y = MAP_Y + y * 0.45

            char = "*"
            if packet.kind == "ddos":
                char = "#"
            elif packet.kind == "query":
                char = "$"
            elif packet.kind == "email":
                char = "@"

            txt = self.font_terminal.render(char, True, packet.color)
            self.screen.blit(txt, (x, y))

    def draw_panel(self):
        panel_rect = pygame.Rect(15, 15, WIDTH-30, HEIGHT-30)
        pygame.draw.rect(self.screen, (5, 8, 15), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, GREEN, panel_rect, 2, border_radius=10)

        title = self.font_huge.render("HACKNET TERMINAL", True, GREEN)
        self.screen.blit(title, (30, 25))

        status = self.font.render(f"THREAT: {self.overall_threat}%", True, RED if self.overall_threat > 60 else GREEN)
        integrity = self.font.render(f"INTEGRITY: {self.network_integrity}%", True, CYAN)
        scenario_text = "IDLE"

        if self.selected_attack:

            active_attack = next(
                (a for a in self.attacks if a.active),
                None
            )

            if active_attack:
                remaining = max(
                    0,
                    int(active_attack.duration - active_attack.elapsed)
                )

                scenario_text = f"{self.selected_attack} ({remaining}s)"

        scenario = self.font.render(
            f"SCENARIO: {scenario_text}",
            True,
            PURPLE
        )
        self.screen.blit(status, (35, 85))
        self.screen.blit(integrity, (250, 85))
        self.screen.blit(scenario, (500, 85))

        terminal_rect = pygame.Rect(25, 130, 900, 520)
        pygame.draw.rect(self.screen, (2, 5, 10), terminal_rect)
        pygame.draw.rect(self.screen, GREEN, terminal_rect, 2)

        scanline_y = int((pygame.time.get_ticks() / 5) % 520)
        pygame.draw.line(self.screen, (30, 90, 30), (27, 132 + scanline_y), (WIDTH-30, 132 + scanline_y), 1)

    def draw_logs(self):
        y = 145

        for line in self.logs:
            color = GREEN
            if "WARNING" in line or "ALERT" in line:
                color = YELLOW
            if "CRITICAL" in line or "compromised" in line.lower():
                color = RED
            if "BLOCKED" in line:
                color = CYAN

            txt = self.font_terminal.render(line[:120], True, color)
            self.screen.blit(txt, (40, y))
            y += 22

        command_prefix = self.font.render("> " + self.terminal.input_text + "_", True, WHITE)
        self.screen.blit(command_prefix, (40, 620))

    def draw_buttons(self):
        pass

    def draw_footer(self):
        footer = self.font_small.render("COMMANDS: help | attacks | analyze | attack ddos 20 | stop | reset", True, MUTED)
        self.screen.blit(footer, (25, HEIGHT -50))

    def draw(self):
        self.screen.fill(BG)
        self.draw_grid()
        self.draw_panel()
        self.draw_links()
        self.draw_packets()
        self.draw_nodes()
        self.draw_logs()
        self.draw_buttons()
        self.draw_footer()
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN:
                    self.execute_command(self.terminal.input_text)
                    self.terminal.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.terminal.input_text = self.terminal.input_text[:-1]
                else:
                    if len(event.unicode) == 1:
                        self.terminal.input_text += event.unicode

    def execute_command(self, command: str):
        cmd = command.strip().lower()

        if not cmd:
            return

        self.log(f"> {cmd}")

        if cmd == "help":
            self.log("Available commands:")
            self.log("scan | status | attacks")
            self.log("attack <type> [duration]")
            self.log("Example: attack ddos 20")
            self.log("analyze <node>")
            self.log("firewall on/off")
            self.log("ids on/off")
            self.log("stop | clear | reset")


        elif cmd == "attacks":

            for attack in self.attacks:
                self.log(
                    f"{attack.name} -> target: {attack.target_node}"
                )

        elif cmd == "clear":

            self.terminal.history.clear()
            self.logs = self.terminal.history

            self.log("[SYS] Terminal buffer cleared.")

        elif cmd.startswith("analyze"):

            parts = cmd.split()

            if len(parts) < 2:
                self.log("Usage: analyze <node>")
                return

            target_name = " ".join(parts[1:]).lower()

            found = None

            for node in self.nodes:

                if node.name.lower() == target_name:
                    found = node
                    break

            if not found:
                self.log("Node not found.")
                return

            self.log(f"NODE: {found.name}")
            self.log(f"STATUS: {found.status.upper()}")
            self.log(f"INTEGRITY: {found.hp}%")

            if found.hp <= 35:
                risk = "CRITICAL"
            elif found.hp <= 70:
                risk = "HIGH"
            else:
                risk = "LOW"

            self.log(f"RISK LEVEL: {risk}")


        elif cmd == "scan":
            self.log("Scanning network nodes...")
            for node in self.nodes:
                self.log(f"{node.name}: {node.status.upper()} | HP {node.hp}%")

        elif cmd == "status":
            self.log(f"Threat level: {self.overall_threat}%")
            self.log(f"Network integrity: {self.network_integrity}%")

        elif cmd.startswith("attack"):

            parts = cmd.split()

            if len(parts) < 2:
                self.log("Usage: attack <type> [duration]")
                return

            attack_name = parts[1]

            duration = None

            if len(parts) >= 3:

                try:
                    duration = int(parts[2])

                except:
                    self.log("Invalid duration.")
                    return

            mapping = {
                "ddos": "DDoS",
                "bruteforce": "Brute Force",
                "phishing": "Phishing",
                "sqli": "SQL Injection"
            }

            if attack_name not in mapping:
                self.log("Unknown attack type.")
                return

            self.launch_attack(
                mapping[attack_name],
                duration
            )

        elif cmd == "firewall on":
            self.toggle_firewall()
            self.log("Firewall enabled.")

        elif cmd == "firewall off":
            self.firewall_enabled = False

            firewall = self.node_by_name("Firewall")
            firewall.status = "normal"

            self.log("Firewall disabled.")

        elif cmd == "ids on":
            self.toggle_ids()
            self.log("IDS enabled.")

        elif cmd == "ids off":
            self.ids_enabled = False

            console = self.node_by_name("Security Console")
            console.status = "normal"

            self.log("IDS disabled.")

        elif cmd == "reset":
            self.reset_system()

        elif cmd == "stop":

            self.auto_attack = False

            self.packets.clear()

            for attack in self.attacks:
                attack.active = False
                attack.elapsed = 0
                attack.timer = 0

            self.selected_attack = None

            self.log("[SYS] All attack operations stopped.")

        else:
            self.log("Unknown command.")

    def run(self):
        self.log("Interactive terminal ready.")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    app = HacknetSimulator()
    app.run()

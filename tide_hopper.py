#!/usr/bin/env python3
"""Tide Hopper — full-colour Python 3 neon frogger/tide-hop arcade for ElbowOS.
Python 3 + pygame. Interactive or headless autoplay reel recorder.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/TIDE_HOPPER_ElbowOS.mp4")
TITLE, HANDLE = "TIDE HOPPER", "x.com/ElbowOS"

# Neon palette — deep teal, lime, magenta, cyan, gold
BG = (8, 18, 28)
LANE = (12, 28, 42)
FROG = (80, 255, 140)
TRAFFIC = [(255, 40, 180), (40, 220, 255), (255, 200, 40), (180, 40, 255)]
GOAL = (40, 255, 200)
TEXT = (240, 255, 240)
SCORE_C = (255, 220, 80)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption("Tide Hopper — ElbowOS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 48, bold=True)
        self.small = pygame.font.SysFont("monospace", 32, bold=True)
        self.reset()

    def reset(self):
        self.frog_x = W // 2
        self.frog_y = H - 180
        self.frog_r = 28
        self.score = 0
        self.lives = 3
        self.lanes = []
        # Vertical lanes from near top to near bottom
        lane_h = 180
        for i in range(6):
            y = 320 + i * lane_h
            direction = 1 if i % 2 == 0 else -1
            speed = random.uniform(2.5, 5.0) * direction
            vehicles = []
            n = random.randint(2, 4)
            for k in range(n):
                vehicles.append({
                    "x": random.randint(0, W),
                    "w": random.randint(80, 150),
                    "color": random.choice(TRAFFIC),
                    "speed": speed
                })
            self.lanes.append({"y": y, "vehicles": vehicles, "speed": speed})
        self.goal_y = 160
        self.hop_cd = 0
        self.frame = 0

    def hop(self, dx=0, dy=-140):
        if self.hop_cd > 0:
            return
        self.frog_x = max(40, min(W - 40, self.frog_x + dx))
        self.frog_y = max(120, min(H - 80, self.frog_y + dy))
        self.hop_cd = 8

    def update(self, auto=False):
        self.frame += 1
        self.hop_cd = max(0, self.hop_cd - 1)
        # Move traffic
        for lane in self.lanes:
            for v in lane["vehicles"]:
                v["x"] += v["speed"]
                if v["x"] > W + 200:
                    v["x"] = -200
                if v["x"] < -200:
                    v["x"] = W + 200
        # Collision
        hit = False
        for lane in self.lanes:
            if abs(self.frog_y - lane["y"]) < 50:
                for v in lane["vehicles"]:
                    if abs(self.frog_x - v["x"]) < (v["w"] // 2 + self.frog_r - 10):
                        hit = True
                        break
            if hit:
                break
        if hit:
            self.lives -= 1
            self.frog_y = H - 180
            self.frog_x = W // 2
            if self.lives <= 0:
                self.score = max(0, self.score - 5)
                self.lives = 3
        # Goal
        if self.frog_y < self.goal_y + 40:
            self.score += 10
            self.frog_y = H - 180
            self.frog_x = W // 2
            for lane in self.lanes:
                lane["speed"] *= 1.05
                for v in lane["vehicles"]:
                    v["speed"] *= 1.05
        # Demo boost for autoplay so score climbs visibly
        if auto and self.frame % 90 == 0 and self.frame > 0:
            self.score += 5
            if self.frog_y > 400:
                self.frog_y -= 100
        # Autoplay AI
        if auto and self.hop_cd == 0 and self.frame % 4 == 0:
            blocked = False
            target_y = self.frog_y - 140
            for lane in self.lanes:
                if abs(target_y - lane["y"]) < 70:
                    for v in lane["vehicles"]:
                        if abs(self.frog_x - v["x"]) < v["w"] // 2 + 50:
                            blocked = True
                            break
                if blocked:
                    break
            if not blocked and self.frog_y > 220:
                self.hop(0, -140)
            else:
                left_clear = True
                right_clear = True
                for lane in self.lanes:
                    if abs(self.frog_y - lane["y"]) < 60:
                        for v in lane["vehicles"]:
                            if abs((self.frog_x - 120) - v["x"]) < v["w"] // 2 + 40:
                                left_clear = False
                            if abs((self.frog_x + 120) - v["x"]) < v["w"] // 2 + 40:
                                right_clear = False
                if left_clear:
                    self.hop(-120, 0)
                elif right_clear:
                    self.hop(120, 0)
                else:
                    self.hop(random.choice([-80, 80]), 0)

    def draw(self):
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, GOAL, (0, 80, W, 100), border_radius=8)
        pygame.draw.rect(self.screen, (20, 80, 60), (0, 80, W, 100), 4, border_radius=8)
        for lane in self.lanes:
            pygame.draw.rect(self.screen, LANE, (0, lane["y"] - 50, W, 100))
            for v in lane["vehicles"]:
                rect = pygame.Rect(int(v["x"] - v["w"] // 2), lane["y"] - 30, v["w"], 60)
                pygame.draw.rect(self.screen, v["color"], rect, border_radius=12)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=12)
        pygame.draw.circle(self.screen, FROG, (int(self.frog_x), int(self.frog_y)), self.frog_r)
        pygame.draw.circle(self.screen, (200, 255, 220), (int(self.frog_x), int(self.frog_y)), self.frog_r, 3)
        pygame.draw.circle(self.screen, (20, 20, 20), (int(self.frog_x - 10), int(self.frog_y - 8)), 6)
        pygame.draw.circle(self.screen, (20, 20, 20), (int(self.frog_x + 10), int(self.frog_y - 8)), 6)
        title_s = self.font.render(TITLE, True, TEXT)
        self.screen.blit(title_s, (W // 2 - title_s.get_width() // 2, 20))
        score_s = self.font.render(f"SCORE {self.score}", True, SCORE_C)
        self.screen.blit(score_s, (40, H - 120))
        lives_s = self.small.render(f"LIVES {self.lives}", True, (255, 120, 120))
        self.screen.blit(lives_s, (W - 280, H - 120))
        handle_s = self.small.render(HANDLE, True, (160, 220, 255))
        self.screen.blit(handle_s, (W // 2 - handle_s.get_width() // 2, H - 60))
        pygame.display.flip()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS),
            "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-movflags", "+faststart",
            "-preset", "fast",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for i in range(frames):
                self.update(auto=True)
                self.draw()
                raw = pygame.image.tostring(self.screen, "RGB")
                proc.stdin.write(raw)
                if i % 30 == 0:
                    print(f"frame {i}/{frames} score={self.score}")
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
            if rc != 0:
                raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

    def play_interactive(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.hop(-100, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.hop(100, 0)
                    elif event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                        self.hop(0, -140)
                    elif event.key == pygame.K_DOWN:
                        self.hop(0, 140)
                    elif event.key == pygame.K_r:
                        self.reset()
            self.update(auto=False)
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

def main():
    g = Game()
    if RECORD:
        g.record()
    elif PLAY:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()

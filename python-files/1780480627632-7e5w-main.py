#!/usr/bin/env python3
"""
NPC Forge v1.0
Professional RPG Character Generator
"""
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from app.application import NPCForgeApplication


def main():
    app = NPCForgeApplication()
    app.run()


if __name__ == "__main__":
    main()

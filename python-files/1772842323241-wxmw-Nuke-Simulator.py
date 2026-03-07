#!/usr/bin/env python3
# Nuke simulator (fictional, educational visualization only)
# Generates a simple blast map and rough casualty estimates using
# cube-root scaling with arbitrary simulation coefficients.

import math
import sys
import random
import argparse
import numpy as np
import matplotlib.pyplot as plt

def parse_args():
    p = argparse.ArgumentParser(description="Simple fictional nuke simulator")
    p.add_argument("--yield-kt", type=float, default=15.0, help="Yield in kilotons")
    p.add_argument("--grid-km", type=float, default=10.0, help="Half-width of map in km")
    p.add_argument("--resolution-m", type=int, default=100, help="Grid resolution in meters")
    p.add_argument("--pop-density", type=float, default=1000, help="Average people per km^2")
    return p.parse_args()

# Simulation coefficients (fictional)
COEFFS = {
    "fireball": 0.12,       # km * Y^(1/3)
    "heavy_damage": 0.6,
    "moderate_damage": 1.2,
    "light_damage": 2.5,
    "thermal_burns": 3.0,
}

# Casualty rates per zone (fictional fractions of population in zone)
CASUALTY_FRAC = {
    "fireball": 0.999,
    "heavy_damage": 0.9,
    "moderate_damage": 0.5,
    "light_damage": 0.2,
    "thermal_burns": 0.15,
}

def radii(yield_kt):
    c = {k: v * (yield_kt ** (1.0/3.0)) for k, v in COEFFS.items()}
    return c

def run_sim(yield_kt, half_km, res_m, pop_density):
    rad = radii(yield_kt)
    res_km = res_m / 1000.0
    size = int((half_km * 2) / res_km)
    if size <= 0:
        raise SystemExit("Grid too small")
    xs = np.linspace(-half_km + res_km/2, half_km - res_km/2, size)
    ys = xs.copy()
    X, Y = np.meshgrid(xs, ys)
    D = np.sqrt(X**2 + Y**2)  # km
    # Create a simple population density map (randomized around mean)
    rng = np.random.default_rng(42)
    pop_per_cell = pop_density * (res_km**2) * rng.normal(1.0, 0.3, size=(size, size))
    pop_per_cell = np.clip(pop_per_cell, 0, None)
    # Determine zones
    zones = np.full(D.shape, "safe", dtype=object)
    for name in ["thermal_burns", "light_damage", "moderate_damage", "heavy_damage", "fireball"]:
        zones[D <= rad[name]] = name
    # Tally
    totals = {}
    for name in ["fireball", "heavy_damage", "moderate_damage", "light_damage", "thermal_burns", "safe"]:
        mask = zones == name
        pop = pop_per_cell[mask].sum()
        casualties = pop * CASUALTY_FRAC.get(name, 0.0)
        totals[name] = {"population": int(pop), "casualties": int(casualties)}
    # Print summary
    print(f"Yield: {yield_kt} kt")
    for k in ["fireball", "heavy_damage", "moderate_damage", "light_damage", "thermal_burns"]:
        print(f"{k:15s} radius = {rad[k]:5.3f} km  pop = {totals[k]['population']:7d}  est casualties = {totals[k]['casualties']:7d}")
    print(f"Outside zones pop = {totals['safe']['population']:7d}")
    # Visualization
    cmap_map = {
        "fireball": (0.3, 0.0, 0.0),
        "heavy_damage": (0.6, 0.0, 0.0),
        "moderate_damage": (1.0, 0.4, 0.0),
        "light_damage": (1.0, 0.8, 0.0),
        "thermal_burns": (1.0, 1.0, 0.6),
        "safe": (0.8, 0.9, 1.0),
    }
    color_grid = np.zeros((size, size, 3))
    for name, col in cmap_map.items():
        mask = zones == name
        color_grid[mask] = col
    fig, ax = plt.subplots(figsize=(6,6))
    ax.imshow(np.flipud(color_grid), extent=[-half_km, half_km, -half_km, half_km])
    ax.set_title(f"Fictional blast map — {yield_kt} kt")
    ax.set_xlabel("km")
    ax.set_ylabel("km")
    # Draw concentric circles
    for name in ["thermal_burns", "light_damage", "moderate_damage", "heavy_damage", "fireball"]:
        circle = plt.Circle((0,0), rad[name], color='k', fill=False, linewidth=0.8)
        ax.add_patch(circle)
    plt.tight_layout()
    plt.show()

def main():
    args = parse_args()
    run_sim(args.yield_kt, args.grid_km, args.resolution_m, args.pop_density)

if __name__ == "__main__":
    main()
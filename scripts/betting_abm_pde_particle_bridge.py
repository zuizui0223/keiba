#!/usr/bin/env python3
"""ABM particle ↔ PDE density bridge for a shared toy stochastic process.

This bridges independent stochastic *particles*, not the horse-level crowded
ABM. Finite-population horse order, lane interference, pacing or calibrated
real-race win/top-three probability are NOT outputs of this bridge.

The particles obey dX = v dt + sqrt(2D) dW. Their probability density solves
the Fokker-Planck PDE: dt(rho) = -v dx(rho) + D dxx(rho).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

STATUS = "SYNTHETIC_INDEPENDENT_PARTICLE_PDE_BRIDGE_NOT_A_HORSE_RACE_MODEL"


def compare_particle_density(*, particles=20000, seed=20261023,
                             dx=0.5, dt=0.04, duration=16.0,
                             drift=0.4, diffusion=1.5,
                             initial_sd=8.0, half_width=100.0):
    """Common drift/diffusion coefficients for particles and PDE.

    The density update uses a conservative upwind advective and centered
    diffusive flux with zero-flux boundary. Diffusion steps are independent
    for each particle; this is the *uncoupled* model only.
    """
    args = [particles, dx, dt, duration, drift, diffusion, initial_sd, half_width]
    if not np.all(np.isfinite(args)) or particles < 1000 or int(particles) != particles:
        raise ValueError("invalid_bridge_numerical_input")
    if dx <= 0 or dt <= 0 or duration <= 0 or initial_sd <= 0 or half_width < 6*initial_sd:
        raise ValueError("invalid_bridge_grid_or_distribution")
    if diffusion < 0 or dt*(abs(drift)/dx + 2*diffusion/(dx*dx)) > 1:
        raise ValueError("unstable_negative_diffusion_or_CFL")
    steps = round(duration / dt)
    if not math.isclose(steps*dt, duration, abs_tol=1e-10):
        raise ValueError("duration_must_be_integer_number_of_steps")
    x = np.arange(-half_width, half_width+dx/2, dx, dtype=float)
    if not math.isclose(x[-1], half_width, abs_tol=1e-9):
        raise ValueError("noninteger_grid_extent")

    # PDE: *exact same* drift & diffusion as the individual motion model
    rho = np.exp(-0.5 * (x/initial_sd)**2)
    rho /= rho.sum()*dx
    for _ in range(steps):
        flux = np.zeros(len(rho)+1)
        # Upwind velocity supports either sign of drift
        adv = drift*np.where(drift >= 0, rho[:-1], rho[1:])
        flux[1:-1] = adv - diffusion*np.diff(rho)/dx
        rho -= dt*np.diff(flux)/dx
    pde_mass = rho.sum()*dx

    # ABM: step each independent agent through the same stochastic law
    rng = np.random.default_rng(seed)
    positions = rng.normal(0, initial_sd, particles)
    scale = math.sqrt(2*diffusion*dt)
    for _ in range(steps):
        positions += drift*dt + scale*rng.standard_normal(particles)

    bins = np.concatenate((x-dx/2, [x[-1]+dx/2]))
    observed_counts, _ = np.histogram(positions, bins=bins)
    missed_agents = int(particles - observed_counts.sum())
    empirical = observed_counts/(particles*dx)

    pde_cdf = np.cumsum(rho)*dx
    abm_cdf = np.cumsum(empirical)*dx
    analytic_mean = drift*duration
    analytic_variance = initial_sd**2+2*diffusion*duration
    sd = math.sqrt(analytic_variance)
    truth = np.exp(-0.5*((x-analytic_mean)/sd)**2)/(sd*math.sqrt(2*math.pi))
    wasserstein_m = float(np.sum(np.abs(pde_cdf-abm_cdf))*dx)
    return {
        "status": STATUS,
        "particle_count": int(particles),
        "draw_seed": seed,
        "CFL": dt*(abs(drift)/dx+2*diffusion/(dx*dx)),
        "steps": steps,
        "grid": {"dx_m": dx, "dt_s": dt, "half_width_m": half_width},
        "stochastic_law": {
            "drift_mps": drift, "diffusion_m2ps": diffusion,
            "initial_position_sd_m": initial_sd,
            "terminal_time_s": duration,
        },
        "pde_mass": float(pde_mass),
        "abm_mass_on_grid": float(empirical.sum()*dx),
        "out_of_domain_particles": missed_agents,
        "expected_mean_m": analytic_mean,
        "pde_mean_m": float((x*rho).sum()*dx/pde_mass),
        "abm_mean_m": float(np.mean(positions)),
        "expected_variance_m2": analytic_variance,
        "abm_variance_m2": float(np.var(positions)),
        "l1_error_abm_vs_pde_density": float(np.sum(np.abs(rho-empirical))*dx),
        "kolmogorov_cdf_error": float(np.max(np.abs(pde_cdf-abm_cdf))),
        "wasserstein1_m": wasserstein_m,
        "l1_error_pde_vs_analytic_gaussian": float(np.sum(np.abs(rho-truth))*dx),
        "pde_nonnegative": bool(np.all(rho >= -1e-12)),
        "limitations": [
            "This is a one-to-one toy Brownian-particle / Fokker-Planck numerical equivalence check.",
            "No horses, no race outcomes, no true GPS data, no pace, no capacity, no social interaction, no race ranking.",
            "Adding crowding changes the SDE and requires a separately justified nonlinear/nonlocal PDE closure.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--particles", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--output", type=Path, default=Path("tmp/abm-pde-particle-bridge.json"))
    args = parser.parse_args()
    result = compare_particle_density(particles=args.particles, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

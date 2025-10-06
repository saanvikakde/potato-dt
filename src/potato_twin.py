# ======================================
# POTATO DIGITAL TWIN MODEL
# --------------------------------------
# Contains simplified equations for potato growth,
# tuber formation, and chamber energy balance.
# ======================================

from dataclasses import dataclass
import numpy as np

# ======================================
# DATA CLASSES: Hold model parameters
# ======================================

@dataclass
class GrowthParamsPotato:
    """Biological constants controlling potato crop growth."""
    LUE_dry_g_per_MJ: float = 1.3        # Light-use efficiency (dry g biomass per MJ absorbed PAR)
    frac_PAR: float = 0.48               # Fraction of incoming radiation that is PAR
    SLA_m2_per_g_dry: float = 0.02       # Specific leaf area (leaf area per gram of dry mass)
    k_extinction: float = 0.65           # Canopy light extinction coefficient (Beer–Lambert)
    dry_to_fresh_ratio: float = 0.20     # Conversion ratio (20% dry matter → 80% water)

    # Cardinal temperatures (°C) for temperature modifier
    base_temp_C: float = 7.0             # Below this → no growth
    opt_temp_C: float = 18.0             # Optimum temperature
    max_temp_C: float = 30.0             # Above this → no growth

    # CO₂ response
    co2_ref_ppm: float = 400.0           # Reference CO₂ concentration
    co2_sat_ppm: float = 1200.0          # Saturating CO₂ concentration

    # Phenology (thermal time thresholds, °C·days)
    tt_emergence: float = 120.0
    tt_tuber_init: float = 350.0
    tt_maturity: float = 1500.0

    # Maintenance respiration fraction (fraction of total biomass respired daily)
    maint_frac_per_day: float = 0.003


@dataclass
class ChamberParams:
    """Physical constants for the growth chamber (heat and energy balance)."""
    heat_capacity_kJ_per_K: float = 1200.0        # Total chamber thermal mass
    U_kJ_per_day_per_K: float = 650.0             # Heat loss coefficient to ambient (per K difference)
    led_power_W: float = 400.0                    # LED power (adds heat)
    other_power_W: float = 80.0                   # Other electrical loads (fans, pumps)
    cooling_capacity_kJ_per_day: float = 25000.0  # Maximum cooling capacity per day
    ambient_temp_C: float = 20.0                  # Surrounding room temperature


@dataclass
class ScenarioPotato:
    """Defines initial and environmental conditions for each simulation run."""
    days: int = 90
    ppfd_umol_m2_s: float = 350.0                 # Light intensity (μmol photons per m² per second)
    photoperiod_h: float = 12.0                   # Hours of light per day
    co2_ppm: float = 800.0                        # CO₂ concentration
    target_chamber_temp_C: float = 18.0           # Target control setpoint for chamber temperature
    initial_leaf_dry_g: float = 1.0               # Initial biomass (leaf)
    ground_area_m2: float = 1.0                   # Surface area per plant (for LAI calculations)

# ======================================
# BASIC HELPER FUNCTIONS
# ======================================

def dli_from_ppfd(ppfd_umol_m2_s: float, photoperiod_h: float) -> float:
    """Convert PPFD and photoperiod to DLI (mol photons/m²/day)."""
    return ppfd_umol_m2_s * photoperiod_h * 3600.0 / 1e6


def molPAR_to_MJ(mol_par: float) -> float:
    """Convert moles of PAR photons to megajoules of energy."""
    return mol_par * 0.219


def temp_modifier(T: float, base: float, opt: float, max_t: float) -> float:
    """Temperature response function (triangle-shaped)."""
    if T <= base or T >= max_t:
        return 0.0
    if T == opt:
        return 1.0
    if T < opt:
        return (T - base) / (opt - base)
    return (max_t - T) / (max_t - opt)


def co2_modifier(co2_ppm: float, ref_ppm: float, sat_ppm: float) -> float:
    """CO₂ effect on photosynthesis (saturating response)."""
    if co2_ppm <= 0:
        return 0.0
    x = (co2_ppm - ref_ppm) / (sat_ppm - ref_ppm + 1e-9)
    return float(np.clip(0.5 + 0.5 * np.clip(x, 0.0, 1.0), 0.0, 1.0))


def canopy_interception_fraction(leaf_dry_g: float, params: GrowthParamsPotato, area_m2: float) -> float:
    """Estimate fraction of incoming light intercepted by leaves (Beer–Lambert law)."""
    LAI = (leaf_dry_g * params.SLA_m2_per_g_dry) / max(area_m2, 1e-9)  # Leaf Area Index
    f = 1.0 - np.exp(-params.k_extinction * LAI)
    return float(np.clip(f, 0.0, 1.0))

# ======================================
# CHAMBER THERMAL MODEL
# ======================================

def chamber_temp_step(T_C: float, chamber: ChamberParams, target_C: float, dt_day: float = 1.0) -> float:
    """Compute next-day chamber temperature from heat balance."""
    # Energy inputs (W → kJ/day)
    Q_led = chamber.led_power_W * 86400.0 / 1000.0
    Q_other = chamber.other_power_W * 86400.0 / 1000.0
    Q_in = Q_led + Q_other

    # Heat loss to ambient
    Q_loss = chamber.U_kJ_per_day_per_K * max(T_C - chamber.ambient_temp_C, 0.0)

    # Cooling load if above target
    Q_cool = 0.0
    if T_C > target_C:
        Q_cool = min(
            chamber.cooling_capacity_kJ_per_day,
            (T_C - target_C) * chamber.heat_capacity_kJ_per_K / dt_day
        )

    # Temperature change (ΔT = (Q_in - Q_loss - Q_cool) / C)
    dT = dt_day * (Q_in - Q_loss - Q_cool) / chamber.heat_capacity_kJ_per_K
    return T_C + dT

# ======================================
# TUBER PARTITIONING LOGIC
# ======================================

def tuber_partition_fraction(tt: float, photoperiod_h: float, params: GrowthParamsPotato) -> float:
    """Estimate the fraction of new biomass allocated to tubers."""
    # Base partition: low before tuber initiation, higher after
    if tt < params.tt_tuber_init:
        base = 0.05
    else:
        base = 0.4

    # Shorter days → stronger tuberization (photoperiod sensitivity)
    photof = np.clip((16.0 - photoperiod_h) / 6.0, 0.0, 1.0)

    # Combine both effects
    return float(np.clip(base + 0.5 * photof, 0.05, 0.9))

# ======================================
# MAIN SIMULATION LOOP
# ======================================

def simulate_potato(
    scn: ScenarioPotato,
    gp: GrowthParamsPotato = GrowthParamsPotato(),
    cp: ChamberParams = ChamberParams()
):
    """Run the potato growth simulation over the specified number of days."""

    # Initialize arrays to store daily values
    days = scn.days
    leaf_dry = np.zeros(days + 1)
    stem_dry = np.zeros(days + 1)
    tuber_dry = np.zeros(days + 1)
    chamber_temp = np.zeros(days + 1)
    thermal_time = np.zeros(days + 1)

    # Initial conditions
    leaf_dry[0] = scn.initial_leaf_dry_g
    chamber_temp[0] = scn.target_chamber_temp_C

    # Daily radiation and energy conversions
    dli = dli_from_ppfd(scn.ppfd_umol_m2_s, scn.photoperiod_h)   # mol/m²/day
    par_MJ = molPAR_to_MJ(dli)                                   # MJ/m²/day

    # Energy accounting
    energy_kWh = np.zeros(days + 1)
    led_kWh_per_day = (cp.led_power_W * scn.photoperiod_h) / 1000.0
    other_kWh_per_day = (cp.other_power_W * 24.0) / 1000.0

    # Daily simulation loop
    for t in range(days):
        # Temperature effect on growth rate
        fT = temp_modifier(chamber_temp[t], gp.base_temp_C, gp.opt_temp_C, gp.max_temp_C)

        # Accumulate thermal time (for phenology)
        dTT = max(0.0, chamber_temp[t] - gp.base_temp_C)
        thermal_time[t + 1] = thermal_time[t] + dTT

        # Light interception
        fI = canopy_interception_fraction(leaf_dry[t], gp, scn.ground_area_m2)

        # Gross photosynthesis (dry g per day)
        gpp_dry = (
            gp.LUE_dry_g_per_MJ
            * (par_MJ * fI)
            * fT
            * co2_modifier(scn.co2_ppm, gp.co2_ref_ppm, gp.co2_sat_ppm)
        )

        # Subtract maintenance respiration
        maintenance = gp.maint_frac_per_day * (leaf_dry[t] + stem_dry[t] + tuber_dry[t])
        net_dry = max(gpp_dry - maintenance, 0.0)

        # Partition new biomass between organs
        frac_tuber = tuber_partition_fraction(thermal_time[t], scn.photoperiod_h, gp)
        frac_leafstem = 1.0 - frac_tuber
        leaf_bias = 0.7 if thermal_time[t] < gp.tt_tuber_init else 0.5  # More leaf early on

        # Allocate to each compartment
        to_tuber = net_dry * frac_tuber
        to_leafstem = net_dry * frac_leafstem
        to_leaf = to_leafstem * leaf_bias
        to_stem = to_leafstem * (1 - leaf_bias)

        # Update state variables
        leaf_dry[t + 1] = max(leaf_dry[t] + to_leaf, 0.0)
        stem_dry[t + 1] = max(stem_dry[t] + to_stem, 0.0)
        tuber_dry[t + 1] = max(tuber_dry[t] + to_tuber, 0.0)

        # Chamber temperature for next day
        chamber_temp[t + 1] = chamber_temp_step(chamber_temp[t], cp, scn.target_chamber_temp_C, 1.0)

        # Energy accumulation (kWh)
        energy_kWh[t + 1] = energy_kWh[t] + led_kWh_per_day + other_kWh_per_day

    # Post-processing
    total_dry = leaf_dry + stem_dry + tuber_dry
    fresh_total = total_dry / max(gp.dry_to_fresh_ratio, 1e-9)  # Convert dry → fresh
    tuber_fresh = tuber_dry / max(0.22, 1e-9)                   # Tuber-specific fresh mass

    # Return results as a dictionary
    return {
        "days": np.arange(days + 1),
        "thermal_time": thermal_time,
        "leaf_dry_g": leaf_dry,
        "stem_dry_g": stem_dry,
        "tuber_dry_g": tuber_dry,
        "fresh_total_g": fresh_total,
        "tuber_fresh_g": tuber_fresh,
        "chamber_temp_C": chamber_temp,
        "cum_energy_kWh": energy_kWh,
        "dli_mol_m2_d": dli,
    }

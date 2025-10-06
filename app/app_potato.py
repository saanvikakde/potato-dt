# --- Import core libraries ---
import streamlit as st                # Streamlit for interactive web app interface
import matplotlib.pyplot as plt       # Matplotlib for plotting graphs
import sys, os                        # Used for adjusting the Python path so imports work

# --- Add project root directory to Python path ---
# This allows importing files from the parent directory (the 'src' folder)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import simulation components from your model file ---
# ScenarioPotato: defines simulation inputs (days, PPFD, etc.)
# GrowthParamsPotato: default biological parameters for potato growth
# ChamberParams: environmental model parameters (heat, cooling, etc.)
# simulate_potato: main function that runs the crop + chamber simulation
from src.potato_twin import ScenarioPotato, GrowthParamsPotato, ChamberParams, simulate_potato

# --- App Title ---
st.title("Mini Digital Twin: Potato (phenology + tuber partition)")

# ===============================
# 1. SCENARIO INPUTS (LEFT SIDEBAR)
# ===============================
# The sidebar sliders let the user adjust growth and environmental parameters interactively

st.sidebar.header("Scenario")

# Core growth conditions
days = st.sidebar.slider("Days", 30, 180, 90, 1)                       # Total simulation length
ppfd = st.sidebar.slider("PPFD (μmol m⁻² s⁻¹)", 150, 800, 350, 10)     # Light intensity
photoperiod = st.sidebar.slider("Photoperiod (h/day)", 10.0, 20.0, 12.0, 0.5)  # Hours of light per day
co2 = st.sidebar.slider("CO₂ (ppm)", 400, 2000, 800, 50)               # Atmospheric CO₂ concentration
target_T = st.sidebar.slider("Target Chamber Temp (°C)", 12.0, 26.0, 18.0, 0.5)  # Desired chamber temp
init_leaf = st.sidebar.slider("Initial Leaf Dry Mass (g)", 0.5, 10.0, 1.0, 0.5)  # Starting plant size
area = st.sidebar.slider("Ground Area (m²)", 0.2, 2.0, 1.0, 0.1)       # Growing area per plant

# ===============================
# 2. ENVIRONMENTAL / CHAMBER INPUTS
# ===============================
st.sidebar.header("Chamber")

# Energy & thermal properties of the growth chamber
led_W = st.sidebar.slider("LED Power (W)", 50, 1500, 400, 10)          # LED lighting power (affects heat)
other_W = st.sidebar.slider("Other Power (W)", 0, 300, 80, 10)         # Other electrical loads (pumps, fans, etc.)
cool_kJ_day = st.sidebar.slider("Cooling Capacity (kJ/day)", 0, 60000, 25000, 1000)  # Cooling ability of system
ambient_T = st.sidebar.slider("Ambient Temp (°C)", 10.0, 35.0, 20.0, 0.5)            # Outside environment temp

# ===============================
# 3. CREATE MODEL INSTANCES
# ===============================
# Define the input scenarios for plant and chamber based on user sliders
scn = ScenarioPotato(
    days=days,
    ppfd_umol_m2_s=ppfd,
    photoperiod_h=photoperiod,
    co2_ppm=co2,
    target_chamber_temp_C=target_T,
    initial_leaf_dry_g=init_leaf,
    ground_area_m2=area
)

# Chamber parameters (energy balance, cooling, etc.)
cp = ChamberParams(
    led_power_W=led_W,
    other_power_W=other_W,
    cooling_capacity_kJ_per_day=cool_kJ_day,
    ambient_temp_C=ambient_T
)

# ===============================
# 4️⃣ RUN SIMULATION
# ===============================
# Call your model with the chosen parameters
res = simulate_potato(scn, GrowthParamsPotato(), cp)

# The result dictionary ('res') contains arrays of daily values:
#   res["days"] → list of days
#   res["tuber_fresh_g"] → daily tuber fresh mass
#   res["thermal_time"] → accumulated heat units
#   res["chamber_temp_C"] → daily chamber temp
#   res["cum_energy_kWh"] → total energy use

# ===============================
# 5️⃣ DISPLAY SUMMARY METRICS
# ===============================
st.subheader("Key Outputs")

# Create three columns for displaying quick summary metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Final Tuber Fresh (g)", f"{res['tuber_fresh_g'][-1]:.0f}")
with col2:
    st.metric("Final Total Fresh (g)", f"{res['fresh_total_g'][-1]:.0f}")
with col3:
    st.metric("Total Energy (kWh)", f"{res['cum_energy_kWh'][-1]:.1f}")

# Display daily light integral (total photons received per day)
st.caption(f"DLI = {res['dli_mol_m2_d']:.2f} mol m⁻² d⁻¹")

# ===============================
# 6️⃣ PLOTS / VISUAL OUTPUTS
# ===============================

# --- Plot 1: Tuber Fresh Mass over time ---
fig1, ax1 = plt.subplots()
ax1.plot(res["days"], res["tuber_fresh_g"])
ax1.set_xlabel("Day")
ax1.set_ylabel("Tuber Fresh Mass (g)")
ax1.set_title("Potato Tuber Fresh Mass")
st.pyplot(fig1)

# --- Plot 2: Accumulated Thermal Time (°C·day) ---
fig2, ax2 = plt.subplots()
ax2.plot(res["days"], res["thermal_time"])
ax2.set_xlabel("Day")
ax2.set_ylabel("Thermal Time (°C·day)")
ax2.set_title("Accumulated Thermal Time")
st.pyplot(fig2)

# --- Plot 3: Chamber Temperature ---
fig3, ax3 = plt.subplots()
ax3.plot(res["days"], res["chamber_temp_C"])
ax3.set_xlabel("Day")
ax3.set_ylabel("Chamber Temp (°C)")
ax3.set_title("Chamber Temperature")
st.pyplot(fig3)

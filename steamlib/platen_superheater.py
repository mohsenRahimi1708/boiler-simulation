# steamlib/platen_superheater.py
# Modular Platen SH: Loads YAML specs, calculates dynamic properties with pyXSteam.
# Focus: Temp control (SP1/SP2) in low load startup.

import yaml
from dataclasses import dataclass
import numpy as np
from pyXSteam.XSteam import XSteam  # For IF97 properties
from typing import Dict, Optional

@dataclass
class PlatenSuperheater:
    """Platen SH class: Geometry from YAML, dynamic calcs."""
    config_file: str = "config/platen_superheater.yaml"
    n_panels: int = 43
    tubes_per_panel: int = 4
    passes_per_panel: int = 8
    pass_length_m: float = 6.0
    total_length_m: float = 50.0
    tube_od_mm: float = 57.0
    tube_id_mm: float = 41.0
    U_W_m2K_low_load: float = 800.0
    setpoint_inlet_C: float = 350.0
    setpoint_outlet_C: float = 410.0

    def __post_init__(self):
        self.load_yaml()
        self.total_tube_count = self.n_panels * self.tubes_per_panel  # 172
        self.cross_section_m2 = np.pi * (self.tube_id_mm / 2000) ** 2  # Per tube
        self.a_total_m2 = self.total_tube_count * self.cross_section_m2
        self.outer_surface_m2 = np.pi * (self.tube_od_mm / 1000) * self.total_length_m * self.total_tube_count

    def load_yaml(self):
        """Load specs from YAML."""
        with open(self.config_file, 'r') as f:
            data = yaml.safe_load(f)
            config = data['platen_superheater']
            self.n_panels = config['structure']['n_panels']
            self.tubes_per_panel = config['structure']['tubes_per_panel']
            self.passes_per_panel = config['structure']['passes_per_panel']
            self.pass_length_m = config['structure']['pass_length_m']
            self.total_length_m = config['structure']['total_length_m']
            self.U_W_m2K_low_load = config['thermal']['U_W_m2K_low_load']
            self.setpoint_inlet_C = config['thermal']['setpoint_inlet_C']
            self.setpoint_outlet_C = config['thermal']['setpoint_outlet_C']
            self.sections = config['sections']  # List of sections with T91 for radiant

    def calculate_properties(self, p_bar: float, t_c: float, steam_flow_th: float) -> Dict:
        """Dynamic: rho, Cp, v, θ, τ with pyXSteam."""
        steam = XSteam()
        p_mpa = p_bar / 10.0
        h_kjkg = steam.t_ph(t_c, p_mpa)
        cp_kjkgk = steam.Cp_pt(p_mpa, t_c)
        rho_kgm3 = 1 / steam.t_pv(t_c, p_mpa)
        m_kgs = steam_flow_th * 1000 / 3600
        v_ms = m_kgs / (rho_kgm3 * self.a_total_m2)
        theta_s = self.total_length_m / v_ms  # Transport delay
        v_total_m3 = self.a_total_m2 * self.total_length_m
        m_kg = rho_kgm3 * v_total_m3
        c_th_jk = m_kg * (cp_kjkgk * 1000)
        ua_wk = self.U_W_m2K_low_load * self.outer_surface_m2
        tau_s = c_th_jk / ua_wk  # Thermal time constant
        return {
            'rho': rho_kgm3, 'cp': cp_kjkgk, 'v': v_ms, 'theta_s': theta_s, 'tau_s': tau_s,
            'h': h_kjkg, 'm_kg': m_kg, 'c_th_jk': c_th_jk, 'ua_wk': ua_wk
        }

    def fopdt_step_response(self, t: np.ndarray, k: float = 0.6, theta_s: float = 0, tau_s: float = 0) -> np.ndarray:
        """FOPDT response for temp rise."""
        y = np.zeros_like(t)
        for i, ti in enumerate(t):
            if ti > theta_s:
                y[i] = k * (1 - np.exp(-(ti - theta_s) / tau_s))
        return y

# Test
if __name__ == "__main__":
    platen = PlatenSuperheater()
    props = platen.calculate_properties(40.0, 350.0, 200.0)
    print("Platen Properties (Low Load):")
    for k, v in props.items():
        print(f"{k}: {v:.2f}")
    t = np.linspace(0, 600, 600)  # 10 min
    response = platen.fopdt_step_response(t, theta_s=props['theta_s'], tau_s=props['tau_s'])
    plt.plot(t/60, response * 50 + 350)  # Example rise 50°C
    plt.xlabel('Time (min)'); plt.ylabel('T_out (°C)'); plt.title('Platen FOPDT Response')
    plt.show()
# steamlib/final_superheater.py
# Modular Final SH: Loads YAML, dynamic calcs with pyXSteam.
# Focus: Final temp control (post-SP2) to 540°C.

import yaml
from dataclasses import dataclass
import numpy as np
from pyXSteam.XSteam import XSteam
from typing import Dict, Optional

@dataclass
class FinalSuperheater:
    """Final SH class: Geometry from YAML, dynamic calcs."""
    config_file: str = "config/final_superheater.yaml"
    n_coils: int = 43
    tubes_per_coil: int = 4
    passes_per_coil: int = 13  # Updated
    pass_length_m: float = 6.0
    total_length_m: float = 85.0  # Updated
    tube_od_mm: float = 57.0
    tube_id_mm: float = 41.0
    U_W_m2K_low_load: float = 900.0
    setpoint_inlet_C: float = 410.0
    setpoint_outlet_C: float = 540.0

    def __post_init__(self):
        self.load_yaml()
        self.total_tube_count = self.n_coils * self.tubes_per_coil  # 172
        self.cross_section_m2 = np.pi * (self.tube_id_mm / 2000) ** 2
        self.a_total_m2 = self.total_tube_count * self.cross_section_m2
        self.outer_surface_m2 = np.pi * (self.tube_od_mm / 1000) * self.total_length_m * self.total_tube_count

    def load_yaml(self):
        """Load specs from YAML."""
        with open(self.config_file, 'r') as f:
            data = yaml.safe_load(f)
            config = data['final_superheater']
            self.n_coils = config['structure']['n_coils']
            self.tubes_per_coil = config['structure']['tubes_per_coil']
            self.passes_per_coil = config['structure']['passes_per_coil']
            self.pass_length_m = config['structure']['pass_length_m']
            self.total_length_m = config['structure']['total_length_m']
            self.U_W_m2K_low_load = config['thermal']['U_W_m2K_low_load']
            self.setpoint_inlet_C = config['thermal']['setpoint_inlet_C']
            self.setpoint_outlet_C = config['thermal']['setpoint_outlet_C']
            self.sections = config['sections']  # T91 for radiant

    def calculate_properties(self, p_bar: float, t_c: float, steam_flow_th: float) -> Dict:
        """Dynamic: rho, Cp, v, θ, τ."""
        steam = XSteam()
        p_mpa = p_bar / 10.0
        h_kjkg = steam.t_ph(t_c, p_mpa)
        cp_kjkgk = steam.Cp_pt(p_mpa, t_c)
        rho_kgm3 = 1 / steam.t_pv(t_c, p_mpa)
        m_kgs = steam_flow_th * 1000 / 3600
        v_ms = m_kgs / (rho_kgm3 * self.a_total_m2)
        theta_s = self.total_length_m / v_ms
        v_total_m3 = self.a_total_m2 * self.total_length_m
        m_kg = rho_kgm3 * v_total_m3
        c_th_jk = m_kg * (cp_kjkgk * 1000)
        ua_wk = self.U_W_m2K_low_load * self.outer_surface_m2
        tau_s = c_th_jk / ua_wk
        return {
            'rho': rho_kgm3, 'cp': cp_kjkgk, 'v': v_ms, 'theta_s': theta_s, 'tau_s': tau_s,
            'h': h_kjkg, 'm_kg': m_kg, 'c_th_jk': c_th_jk, 'ua_wk': ua_wk
        }

    def fopdt_step_response(self, t: np.ndarray, k: float = 0.7, theta_s: float = 0, tau_s: float = 0) -> np.ndarray:
        """FOPDT for Final (higher gain 0.7 convective)."""
        y = np.zeros_like(t)
        for i, ti in enumerate(t):
            if ti > theta_s:
                y[i] = k * (1 - np.exp(-(ti - theta_s) / tau_s))
        return y

# Test
if __name__ == "__main__":
    final = FinalSuperheater()
    props = final.calculate_properties(40.0, 410.0, 200.0)
    print("Final Properties (Low Load):")
    for k, v in props.items():
        print(f"{k}: {v:.2f}")
    t = np.linspace(0, 600, 600)
    response = final.fopdt_step_response(t, theta_s=props['theta_s'], tau_s=props['tau_s'])
    plt.plot(t/60, response * 80 + 410)  # Example rise 80°C to 540°C
    plt.xlabel('Time (min)'); plt.ylabel('T_out (°C)'); plt.title('Final FOPDT Response')
    plt.show()
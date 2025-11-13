import numpy as np

class BoilerModel:
    def __init__(self, steam_pressure, steam_temperature, fuel_flow_rate):
        self.steam_pressure = steam_pressure
        self.steam_temperature = steam_temperature
        self.fuel_flow_rate = fuel_flow_rate

    def calculate_efficiency(self):
        # مثال ساده برای محاسبه راندمان
        heat_input = self.fuel_flow_rate * 42000  # فرضی: MJ/h
        heat_output = self.steam_pressure * self.steam_temperature * 0.85  # فرضی
        efficiency = (heat_output / heat_input) * 100
        return efficiency

    def simulate_spray(self, spray_angle, spray_pressure):
        # شبیه‌سازی ساده اسپری
        spread = spray_pressure * np.tan(np.radians(spray_angle))
        return spread

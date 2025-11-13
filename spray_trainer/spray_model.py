import matplotlib.pyplot as plt

class SpraySimulator:
    def __init__(self, pressure, angle, flow_rate):
        self.pressure = pressure
        self.angle = angle
        self.flow_rate = flow_rate

    def simulate(self):
        spread = self.pressure * self.flow_rate * 0.1
        return spread

    def plot_spray_pattern(self):
        x = [i for i in range(10)]
        y = [self.simulate() * (1 - abs(i - 5)/5) for i in x]
        plt.plot(x, y)
        plt.title("Spray Pattern")
        plt.xlabel("Distance")
        plt.ylabel("Spray Intensity")
        plt.grid(True)
        plt.show()

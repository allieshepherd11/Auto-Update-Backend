import numpy as np
from scipy.optimize import curve_fit


def getArpsParams(df):
    def hyperbolic_arps(t, qi, Di, b):
        return qi / ((1 + b * Di * t)**(1/b))

    time_days = np.array([30, 60, 90, 120, 150])
    production_rates = np.array([900, 750, 650, 550, 500])

    popt, pcov = curve_fit(hyperbolic_arps, time_days, production_rates, p0=[1000, 0.5, 0.5])

    qi_fitted, Di_fitted, b_fitted = popt

    print(f"Fitted qi: {qi_fitted:.2f} bbl/day")
    print(f"Fitted Di: {Di_fitted:.4f} 1/day")
    print(f"Fitted b: {b_fitted:.4f}")

    predicted_rates = hyperbolic_arps(time_days, qi_fitted, Di_fitted, b_fitted)

    for t, rate in zip(time_days, predicted_rates):
        print(f"Predicted production rate at {t} days: {rate:.2f} bbl/day")

getArpsParams(5)
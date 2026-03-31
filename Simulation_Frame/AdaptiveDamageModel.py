class AdaptiveDamageModel:

    def __init__(self, alpha_max=5.0, beta_max=5.0):
        self.alpha_max = alpha_max
        self.beta_max = beta_max

    @staticmethod
    def clip(x, lo=0.0, hi=1.0):
        return max(lo, min(x, hi))

    def predict_time(self, data):
        a = data["adaptive"]
        return a["T0"] * (1 + a["alpha"] * (1 - a["h"]))

    def observe_traversal(self, data, T_obs):
        T_pred = self.predict_time(data)
        return (T_obs - T_pred) / data["adaptive"]["T0"]

    def update_alpha(self, data, T_obs):
        a = data["adaptive"]
        T_pred = self.predict_time(data)

        grad = ((T_obs - T_pred) / a["T0"]) * (1 - a["h"])
        a["alpha"] = self.clip(
            a["alpha"] + a["eta_alpha"] * grad,
            0.0,
            self.alpha_max
        )

    def update_health(self, data, T_obs):
        a = data["adaptive"]
        h_before = a["h"]

        damage = a["mu"] * a["beta"] + \
                 a["nu"] * ((T_obs - a["T0"]) / a["T0"])

        a["h"] = self.clip(h_before - damage)

        return a["h"] - h_before

    def update_beta(self, data, delta_h):
        a = data["adaptive"]

        if delta_h < 0 and a["h"] > 0:
            grad = (-delta_h) / a["h"]
            a["beta"] = self.clip(
                a["beta"] + a["eta_beta"] * grad,
                0.0,
                self.beta_max
            )

    def expected_cost(self, data):
        a = data["adaptive"]
        T_pred = self.predict_time(data)

        return T_pred * (1 + a["lambda_risk"] * (1 - a["h"]))

    def on_traversal(self, data, T_obs):
        self.update_alpha(data, T_obs)
        delta_h = self.update_health(data, T_obs)
        self.update_beta(data, delta_h)

        data["heuristic"] = self.expected_cost(data)

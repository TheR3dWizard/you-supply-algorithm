from typing import Optional,List
from .node import Node
class RoadEdge:
    self.u:Node
    self.v:Node
    self.T0:float
    self.h:float
    self.alpha:float
    self.beta:float
    self.lastupdatedtime:Optional[float]
    self.distance:float
    def __init__(self, u:Node, v:Node, T0:float, h:float, alpha:float, beta:float, lastupdatedtime:Optional[float]=None):
        self.u = u
        self.v = v
        self.T0 = T0
        self.h = h
        self.alpha = alpha
        self.beta = beta
        self.lastupdatedtime = lastupdatedtime
        self.distance = self.get_distance()
        
    def get_distance(self) -> float:
        return 10.0 #TODO: Implement actual distance calculation
    
    '''
    predict_time()
    observe_traversal(T_obs)
    update_alpha(T_obs)
    update_health(T_obs)
    update_beta(delta_h)
    expected_cost()
    '''
    
    def clip(self, x, lo=0.0, hi=1.0) -> float:
        return max(lo, min(x, hi))
    
    def predict_time(self):
        return self.T0 * (1 + self.alpha * (1 - self.h))

    def observe_traversal(self, T_obs):
        T_pred = self.predict_time()
        error = (T_obs - T_pred) / self.T0
        return error
    
    def update_alpha(self, T_obs):
        T_pred = self.predict_time()
        grad = ((T_obs - T_pred) / self.T0) * (1 - self.h)
        self.alpha = self.clip(self.alpha + self.eta_alpha * grad, 0.0, self.alpha_max)
    
    def update_health(self, T_obs):
        h_before = self.h
        damage = self.mu * self.beta + self.nu * ((T_obs - self.T0) / self.T0)
        self.h = self.clip(self.h - damage)
        return self.h - h_before

    def update_beta(self, delta_h):
        if delta_h < 0 and self.h > 0:
            grad = (-delta_h) / self.h
            self.beta = self.clip(self.beta + self.eta_beta * grad, 0.0, self.beta_max)
    
    def traverse(self, T_obs):
        self.update_alpha(T_obs)
        delta_h = self.update_health(T_obs)
        self.update_beta(delta_h)
        return delta_h

        
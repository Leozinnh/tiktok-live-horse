import math
from typing import Tuple

class TrackGeometry:
    """
    Geometria de pista de hipódromo em formato de oval esportivo com 1.000 metros de comprimento.
    Possui duas retas principais de 300m cada e duas curvas de 200m cada (raio ~63.66m).
    """
    def __init__(self, track_length: float = 1000.0, lane_width: float = 2.4):
        self.track_length = track_length
        self.lane_width = lane_width
        
        # Parâmetros da oval
        self.straight_len = 300.0
        self.curve_len = 200.0
        self.radius = self.curve_len / math.pi  # ~63.66 metros
        # O centro da pista está em self.radius (63.66m).
        # A largura total da pista é 22m (de 52.66m a 74.66m).
        # Centralizamos as 8 raias (cada uma com 2.4m) a partir de radius - 8.4m
        # Raia 1 = 55.26m, Raia 8 = 72.06m (todas 100% dentro dos limites da pista)
        self.base_lane_r = self.radius - 8.4

    def _compute_point(self, dist_mod: float, r: float) -> Tuple[float, float]:
        # Segmento 1: Reta Principal (Largada / Chegada) [0 .. 300]
        if dist_mod <= self.straight_len:
            t = dist_mod / self.straight_len
            x = -self.straight_len / 2.0 + t * self.straight_len
            z = r
            return x, z
            
        # Segmento 2: Curva 1 [300 .. 500]
        elif dist_mod <= self.straight_len + self.curve_len:
            curve_dist = dist_mod - self.straight_len
            angle = (curve_dist / self.curve_len) * math.pi
            theta = (math.pi / 2.0) - angle
            center_x = self.straight_len / 2.0
            x = center_x + r * math.cos(theta)
            z = r * math.sin(theta)
            return x, z
            
        # Segmento 3: Reta Oposta [500 .. 800]
        elif dist_mod <= 2 * self.straight_len + self.curve_len:
            t = (dist_mod - (self.straight_len + self.curve_len)) / self.straight_len
            x = self.straight_len / 2.0 - t * self.straight_len
            z = -r
            return x, z
            
        # Segmento 4: Curva 2 (Entrada da Reta Final) [800 .. 1000]
        else:
            curve_dist = dist_mod - (2 * self.straight_len + self.curve_len)
            angle = (curve_dist / self.curve_len) * math.pi
            theta = -math.pi / 2.0 - angle
            center_x = -self.straight_len / 2.0
            x = center_x + r * math.cos(theta)
            z = r * math.sin(theta)
            return x, z

    def get_coordinates(self, distance: float, lane: int = 1) -> Tuple[float, float, float, float]:
        """
        Retorna (x, y, z, rotation_y) no espaço Three.js.
        y é a elevação (0.0).
        rotation_y é o ângulo tangencial contínuo de avanço do cavalo.
        """
        dist_mod = distance % self.track_length
        # Ajuste de raio pela raia (raia 1 é a interna, raia 8 é a externa)
        lane_idx = max(1, min(8, lane))
        r = self.base_lane_r + (lane_idx - 1) * self.lane_width

        x, z = self._compute_point(dist_mod, r)
        next_dist = (dist_mod + 0.25) % self.track_length
        x_next, z_next = self._compute_point(next_dist, r)

        dx = x_next - x
        dz = z_next - z
        rot_y = math.atan2(dx, dz)
        return (x, 0.0, z, rot_y)

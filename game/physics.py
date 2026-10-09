import math
from typing import Tuple

class TrackGeometry:
    """
    Geometria de pista de hipódromo em formato de oval esportivo com 3.000 metros de comprimento.
    Possui duas retas principais de 900m cada e duas curvas de 600m cada (raio ~190.99m).
    """
    def __init__(self, track_length: float = 3000.0, lane_width: float = 3.2):
        self.track_length = track_length
        self.lane_width = lane_width

        # Parâmetros da oval (o triplo do oval original de 1.000m — mesma forma)
        self.straight_len = 900.0
        self.curve_len = 600.0
        self.radius = self.curve_len / math.pi  # ~190.99 metros
        # O centro da pista está em self.radius (190.99m).
        # A largura total da pista é 28m (de 176.99m a 204.99m) — a largura NÃO
        # cresceu junto: retas e curvas triplicaram, as raias continuam 3.2m.
        # Centralizamos as 8 raias (cada uma com 3.2m de largura) a partir de radius - 11.2m:
        # Raia 1 = 179.79m, Raia 8 = 202.19m (todas 100% dentro dos limites com margem de 2.8m das cercas)
        self.base_lane_r = self.radius - 11.2

    def _compute_point(self, dist_mod: float, r: float) -> Tuple[float, float]:
        # Segmento 1: Reta Principal (Largada / Chegada) [0 .. 900]
        if dist_mod <= self.straight_len:
            t = dist_mod / self.straight_len
            x = -self.straight_len / 2.0 + t * self.straight_len
            z = r
            return x, z

        # Segmento 2: Curva 1 [900 .. 1500]
        elif dist_mod <= self.straight_len + self.curve_len:
            curve_dist = dist_mod - self.straight_len
            angle = (curve_dist / self.curve_len) * math.pi
            theta = (math.pi / 2.0) - angle
            center_x = self.straight_len / 2.0
            x = center_x + r * math.cos(theta)
            z = r * math.sin(theta)
            return x, z

        # Segmento 3: Reta Oposta [1500 .. 2400]
        elif dist_mod <= 2 * self.straight_len + self.curve_len:
            t = (dist_mod - (self.straight_len + self.curve_len)) / self.straight_len
            x = self.straight_len / 2.0 - t * self.straight_len
            z = -r
            return x, z

        # Segmento 4: Curva 2 (Entrada da Reta Final) [2400 .. 3000]
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

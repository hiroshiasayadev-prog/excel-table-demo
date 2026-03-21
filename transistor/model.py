from typing import Callable
import numpy as np
import copy

class TransistorModel:
    """トランジスタモデル"""

    def __init__(self):
        """パラメータ (GaAs/AlGaAs HEMT)"""
        self.mu = 0.6        # 移動度 [m^2/V·s]  GaAsは高い
        self.v_sat = 1.2e5   # 飽和速度 [m/s]
        self.eps = 12.9 * 8.854e-12  # GaAs誘電率
        self.d = 30e-9       # AlGaAsバリア厚 [m]
        self.W = 100e-6      # ゲート幅 [m]
        self.L = 1e-6        # ゲート長 [m]
        self.Vth = -0.5      # 閾値電圧（depletion-mode）

    def get_k_2deg(self) -> float:
        """シート電荷係数"""
        return self.eps * self.W / (self.d * self.L)
    
    def Id(self, VGS: float, VDS: float) -> float:
        Vov = VGS - self.Vth
        if Vov <= 0:
            return 0.0
        # 速度飽和モデル
        num = self.mu * self.get_k_2deg() * Vov * VDS
        den = 1 + VDS / (self.v_sat * self.L / self.mu)  # = 1 + mu*VDS/(v_sat*L)
        # 飽和電圧
        Vdsat = (Vov * self.v_sat * self.L) / (self.mu * Vov + self.v_sat * self.L)
        if VDS >= Vdsat:
            VDS_c = Vdsat
            num = self.mu * self.get_k_2deg() * Vov * VDS_c
            den = 1 + VDS_c / (self.v_sat * self.L / self.mu)
        return num / den
    
    @property
    def Id_v(self) -> Callable[[float | np.ndarray, float | np.ndarray], np.ndarray]:
        return np.vectorize(self.Id)
    

class TransistorHysteresisModel:
    """
    履歴依存(hysteresis)を持つラッパーモデル。

    - base_model を内部に保持
    - trap occupancy z in [0, 1] を状態として持つ
    - 実効閾値: Vth_eff = base_model.Vth + alpha_vth * z
    - Id_step() は状態更新込み
    - Id() は現在状態での瞬時電流のみ計算（状態更新なし）
    """

    def __init__(
        self,
        base_model: TransistorModel,
        *,
        alpha_vth: float = 0.25,
        tau_fill: float = 1e-3,
        tau_empty: float = 5e-3,
        z0: float = 0.0,
        copy_base_model: bool = True,
    ):
        self.base_model = copy.deepcopy(base_model) if copy_base_model else base_model

        self.alpha_vth = alpha_vth
        self.tau_fill = tau_fill
        self.tau_empty = tau_empty
        self.z = float(np.clip(z0, 0.0, 1.0))

    def initialize_state(self, z0: float = 0.0) -> None:
        self.z = float(np.clip(z0, 0.0, 1.0))

    @property
    def Vth_eff(self) -> float:
        return self.base_model.Vth + self.alpha_vth * self.z

    def z_inf(self, VGS: float, VDS: float) -> float:
        """
        平衡トラップ占有率。
        高 VGS・高 VDS ほど trap が埋まりやすい簡易モデル。
        """
        x = 4.0 * (VGS - 0.0) + 1.5 * max(VDS, 0.0)
        return float(1.0 / (1.0 + np.exp(-x)))

    def update_state(self, VGS: float, VDS: float, dt: float) -> None:
        z_target = self.z_inf(VGS, VDS)
        tau = self.tau_fill if z_target > self.z else self.tau_empty

        self.z += (z_target - self.z) * (1.0 - np.exp(-dt / tau))
        self.z = float(np.clip(self.z, 0.0, 1.0))

    def Id(self, VGS: float, VDS: float) -> float:
        """
        現在の内部状態 z を使った瞬時電流。
        状態更新はしない。
        """
        Vov = VGS - self.Vth_eff
        if Vov <= 0:
            return 0.0

        m = self.base_model
        num = m.mu * m.get_k_2deg() * Vov * VDS
        den = 1 + VDS / (m.v_sat * m.L / m.mu)

        Vdsat = (Vov * m.v_sat * m.L) / (m.mu * Vov + m.v_sat * m.L)
        if VDS >= Vdsat:
            VDS_c = Vdsat
            num = m.mu * m.get_k_2deg() * Vov * VDS_c
            den = 1 + VDS_c / (m.v_sat * m.L / m.mu)

        return num / den

    def Id_step(self, VGS: float, VDS: float, dt: float) -> float:
        """
        1ステップ時間発展させてから電流を返す。
        sweep では通常これを使う。
        """
        self.update_state(VGS, VDS, dt)
        return self.Id(VGS, VDS)

    def sweep_vgs(
        self,
        vgs_values: np.ndarray,
        VDS: float,
        dt: float,
        *,
        initialize_state: bool = False,
        z0: float = 0.0,
    ) -> np.ndarray:
        if initialize_state:
            self.initialize_state(z0)

        ids = []
        for vgs in vgs_values:
            ids.append(self.Id_step(float(vgs), float(VDS), dt))
        return np.asarray(ids)

    def sweep_vds(
        self,
        vds_values: np.ndarray,
        VGS: float,
        dt: float,
        *,
        initialize_state: bool = False,
        z0: float = 0.0,
    ) -> np.ndarray:
        if initialize_state:
            self.initialize_state(z0)

        ids = []
        for vds in vds_values:
            ids.append(self.Id_step(float(VGS), float(vds), dt))
        return np.asarray(ids)

    @property
    def Id_v(self) -> Callable[[float | np.ndarray, float | np.ndarray], np.ndarray]:
        """
        注意:
        これは状態更新なしのベクトル化版。
        hysteresis を反映した sweep をしたいなら sweep_vgs/sweep_vds を使うこと。
        """
        return np.vectorize(self.Id)
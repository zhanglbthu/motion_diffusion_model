r"""
    View 3D rotations in real-time using pybullet (numpy quaternion).
"""


__all__ = ['RotationViewer']


import time
import pybullet as p
import pybullet_data
import numpy as np
from typing import List, Tuple, Union


class RotationViewer:
    r"""
    View 3D rotations in real-time / offline.
    """

    camera_distance = 5

    def __init__(self, n=1, overlap=False, order='xyzw'):
        r"""
        :param n: Number of rotations to simultaneously show.
        """
        assert order == 'xyzw' or order == 'wxyz', 'Only support xyzw or wxyz.'
        self.n = n
        self.interval = 0 if overlap else 1.2
        self.physics_client = 0
        self.objs = []
        self.wfirst = order == 'wxyz'

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        r"""
        Connect to the viewer.
        """
        self.physics_client = p.connect(p.GUI)
        p.configureDebugVisualizer(flag=p.COV_ENABLE_Y_AXIS_UP, enable=1)
        p.resetDebugVisualizerCamera(cameraDistance=self.camera_distance, cameraYaw=0, cameraPitch=-30,
                                     cameraTargetPosition=[0, 0, 0])
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        offset = (self.n - 1) * self.interval / 2
        self.objs = [p.loadURDF('duck_vhacd.urdf', [-i * self.interval + offset, 0, 0], globalScaling=10) for i in range(self.n)]

    def disconnect(self):
        r"""
        Disconnect to the viewer.
        """
        if p.isConnected(self.physics_client):
            p.disconnect(self.physics_client)

    def update_all(self, quaternions: Union[List[np.ndarray], Tuple[np.ndarray]]):
        r"""
        Update all quaternions together.

        :param quaternions: List of arrays in shape [4] for quaternions.
        """
        assert len(quaternions) == self.n, 'Number of rotations is not equal to the init value in RotationViewer.'
        for i, q in enumerate(quaternions):
            self.update(q, i)

    def update(self, quaternion: np.ndarray, index=0):
        r"""
        Update the ith rotation.

        :param quaternion: Array in shape [4] for a quaternion.
        :param index: The index of the rotation to update.
        """
        assert p.isConnected(self.physics_client), 'RotationViewer is not connected.'
        position, _ = p.getBasePositionAndOrientation(self.objs[index])
        quaternion = np.array(quaternion)[[1, 2, 3, 0]] if self.wfirst else np.array(quaternion)
        p.resetBasePositionAndOrientation(self.objs[index], position, quaternion)

    def view_offline(self, quaternions: Union[List[np.ndarray], Tuple[np.ndarray]], fps=60):
        r"""
        View 3D rotation sequences offline.

        :param quaternions: List of arrays in shape [seq_len, 4] for quaternions.
        :param fps: Sequence fps.
        """
        quaternions = [q.reshape((-1, 4)) for q in quaternions]
        seq_len = quaternions[0].shape[0]
        assert all([q.shape[0] == seq_len for q in quaternions]), 'Different sequence lengths for RotationViewer'
        is_connected = p.isConnected(self.physics_client)
        if not is_connected:
            self.connect()
        for i in range(seq_len):
            t = time.time()
            self.update_all([q[i] for q in quaternions])
            time.sleep(max(t + 1 / fps - time.time(), 0))
        if not is_connected:
            self.disconnect()

    def print_text(self, text: str, position: List[float] = [0, 0, 1],
                   color: Tuple[float, float, float] = (1, 1, 1),
                   textSize: float = 1.2, lifeTime: float = 0):
        """
        在屏幕上显示指定文本。

        :param text: 要显示的文本内容。
        :param position: 文本显示的位置（世界坐标系）。
        :param color: 文本颜色，格式为 (R, G, B)。
        :param textSize: 文本大小。
        :param lifeTime: 文本显示的持续时间，0 表示永久显示。
        """
        p.removeAllUserDebugItems()
        p.addUserDebugText(text, position, textColorRGB=color, textSize=textSize, lifeTime=lifeTime)


# example
if __name__ == '__main__':
    rotations1 = np.linspace([0, 0, 0, 1], [1, 0, 0, 0], num=60)
    rotations2 = np.linspace([0, 0, 0, 1], [0, 1, 0, 0], num=60)

    # offline
    RotationViewer(2).view_offline([rotations1, rotations2], fps=30)

    # online
    with RotationViewer(2) as viewer:
        for r1, r2 in zip(rotations1, rotations2):
            viewer.update_all([r1, r2])
            time.sleep(1 / 30)

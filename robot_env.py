from typing import Optional

import numpy as np
import zmq
import gymnasium as gym
from gymnasium import spaces


class RobotArmEnv(gym.Env):
    """
    Gym environment that communicates with robot_server.py over ZMQ.

    action_space:       Box(-1, 1, shape=(3,))  — [base, shoulder, elbow]
    observation_space:  Box(-inf, inf, shape=(2,)) — [x_steps, y_steps]

    Subclass and override compute_reward() and is_terminated() to implement
    task-specific logic. The server is a stateless hardware backend.
    """

    def __init__(self, host='localhost', port=5555):
        super().__init__()

        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(2,), dtype=np.float32
        )

        self._host = host
        self._port = port
        self._context = zmq.Context()
        self._socket: Optional[zmq.Socket] = None
        self._connect()

    def _connect(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.setsockopt(zmq.RCVTIMEO, 5000)   # 5s receive timeout
        self._socket.setsockopt(zmq.LINGER, 0)         # don't block on close
        self._socket.connect(f"tcp://{self._host}:{self._port}")

    def _send_recv(self, message, retries=3) -> dict:
        """Send a JSON message and return the JSON reply. Lazy Pirate reconnect on timeout."""
        for attempt in range(retries):
            assert self._socket is not None
            try:
                self._socket.send_json(message)
                reply: dict = self._socket.recv_json()  # type: ignore[assignment]
                return reply
            except zmq.Again:
                if attempt < retries - 1:
                    print(f"ZMQ timeout, reconnecting (attempt {attempt + 1}/{retries})...")
                    self._connect()
                else:
                    raise
        raise RuntimeError("unreachable")

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        reply = self._send_recv({'cmd': 'reset'})
        obs = np.array(reply['obs'], dtype=np.float32)
        info = reply.get('info', {})
        return obs, info

    def step(self, action):
        reply = self._send_recv({'cmd': 'step', 'action': action.tolist()})
        obs = np.array(reply['obs'], dtype=np.float32)
        reward = self.compute_reward(obs, action)
        terminated = self.is_terminated(obs)
        truncated = False
        return obs, reward, terminated, truncated, {}

    def close(self):
        try:
            self._send_recv({'cmd': 'stop'})
        except Exception:
            pass  # Best-effort stop; server may already be down
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        self._context.term()

    # --- Override these in subclasses ---

    def compute_reward(self, obs, action) -> float:
        """Task-specific reward. Override in subclass."""
        return 0.0

    def is_terminated(self, obs) -> bool:
        """Task-specific termination condition. Override in subclass."""
        return False

import torch
from torch.optim import RMSprop, Adam

from maro.rl.model import DiscreteACBasedNet, VNet
from .networks import QuantumFullyConnected
from maro.rl.policy import DiscretePolicyGradient
from maro.rl.training.algorithms import PPOParams, PPOTrainer

actor_net_conf = {
    "hidden_dims": [256, 128, 64],
    "activation": torch.nn.Tanh,
    "softmax": True,
    "batch_norm": False,
    "head": True,
}
critic_net_conf = {
    "hidden_dims": [256, 128, 64],
    "output_dim": 1,
    "activation": torch.nn.LeakyReLU,
    "softmax": False,
    "batch_norm": True,
    "head": True,
}

actor_learning_rate = 0.001
critic_learning_rate = 0.001

class MyActorNet(DiscreteACBasedNet):
    def __init__(self, state_dim: int, action_num: int) -> None:
        super(MyActorNet, self).__init__(state_dim=state_dim, action_num=action_num)
        self._actor = QuantumFullyConnected(input_dim=state_dim, output_dim=action_num, **actor_net_conf)
        self._optim = Adam(self._actor.parameters(), lr=actor_learning_rate)

    def _get_action_probs_impl(self, states: torch.Tensor) -> torch.Tensor:
        return self._actor(states)

class MyCriticNet(VNet):
    def __init__(self, state_dim: int) -> None:
        super(MyCriticNet, self).__init__(state_dim=state_dim)
        self._critic = QuantumFullyConnected(input_dim=state_dim, **critic_net_conf)
        self._optim = RMSprop(self._critic.parameters(), lr=critic_learning_rate)

    def _get_v_values(self, states: torch.Tensor) -> torch.Tensor:
        return self._critic(states).squeeze(-1)
    
def get_ppo_policy(state_dim: int, action_num: int, name: str) -> DiscretePolicyGradient:
    return DiscretePolicyGradient(name=name, policy_net=MyActorNet(state_dim, action_num))


def get_ppo(state_dim: int, name: str) -> PPOTrainer:
    return PPOTrainer(
        name=name,
        reward_discount=0.0,
        params=PPOParams(
            get_v_critic_net_func=lambda: MyCriticNet(state_dim),
            grad_iters=10,
            critic_loss_cls=torch.nn.SmoothL1Loss,
            lam=0.0,
            clip_ratio=0.1,
        ),
    )
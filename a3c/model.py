import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from SpectralNormLayer import SNConv2d, SNLinear


def normalized_columns_initializer(weights, std=1.0):
    out = torch.randn(weights.size())
    out *= std / torch.sqrt(out.pow(2).sum(1, keepdim=True))
    return out


def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        weight_shape = list(m.weight.data.size())
        fan_in = np.prod(weight_shape[1:4])
        fan_out = np.prod(weight_shape[2:4]) * weight_shape[0]
        w_bound = np.sqrt(6. / (fan_in + fan_out))
        m.weight.data.uniform_(-w_bound, w_bound)
        m.bias.data.fill_(0)
    elif classname.find('Linear') != -1:
        weight_shape = list(m.weight.data.size())
        fan_in = weight_shape[1]
        fan_out = weight_shape[0]
        w_bound = np.sqrt(6. / (fan_in + fan_out))
        m.weight.data.uniform_(-w_bound, w_bound)
        m.bias.data.fill_(0)


class ActorCritic(torch.nn.Module):
    def __init__(self, num_inputs, action_space, use_sn):
        super(ActorCritic, self).__init__()
        if use_sn:
            Conv2d, Linear = SNConv2d, SNLinear
        else:
            Conv2d, Linear = nn.Conv2d, nn.Linear

        self.conv1 = Conv2d(num_inputs, 32, 3, stride=2, padding=1)
        self.conv2 = Conv2d(32, 32, 3, stride=2, padding=1)
        self.conv3 = Conv2d(32, 32, 3, stride=2, padding=1)
        self.conv4 = Conv2d(32, 32, 3, stride=2, padding=1)

        self.lin = Linear(32 * 3 * 3, 256)

        num_outputs = action_space.n
        self.critic_linear = Linear(256, 1)
        self.actor_linear = Linear(256, num_outputs)

        self.apply(weights_init)
        self.actor_linear.weight.data = normalized_columns_initializer(
            self.actor_linear.weight.data, 0.01)
        self.actor_linear.bias.data.fill_(0)
        self.critic_linear.weight.data = normalized_columns_initializer(
            self.critic_linear.weight.data, 1.0)
        self.critic_linear.bias.data.fill_(0)

        self.lin.bias.data.fill_(0)

        self.train()

    def forward(self, inputs):
        x = F.elu(self.conv1(inputs))
        x = F.elu(self.conv2(x))
        x = F.elu(self.conv3(x))
        x = F.elu(self.conv4(x))

        x = x.view(-1, 32 * 3 * 3)
        x = self.lin(x)
        return self.critic_linear(x), self.actor_linear(x)
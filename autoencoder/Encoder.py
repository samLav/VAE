import math
import torch.nn as nn
from torch.autograd import Variable

from loader import load_svhn
from modules import View, n_maps


def conv_encoder(shape, dim_h, batch_norm, dropout, nonlinearity, min_dim):
    model = nn.Sequential()
    n_convolution = int(math.log(shape[2] / min_dim, 2))
    f_size, stride, pad = 4, 2, 1
    for c in range(n_convolution):
        n_maps_in = n_maps(c, dim_h, shape[1])
        n_maps_out = n_maps(c+1, dim_h, shape[1])
        conv = nn.Conv2d(n_maps_in, n_maps_out, f_size, stride, pad)
        name = 'conv_%s_%s' % (n_maps_in, n_maps_out)
        model.add_module(name, conv)
        if batch_norm:
            model.add_module(name + '_bn', nn.BatchNorm2d(n_maps_out))
        if dropout:
            model.add_module(name + '_do', nn.Dropout2d(p=dropout))
        model.add_module('%s_%s' % (name, nonlinearity), nonlinearity)
    cat_size = 2 * (n_convolution - 1) * dim_h * (shape[2] / 2 ** n_convolution) * (shape[3] / (2 ** n_convolution))
    model.add_module('flatten', View(-1, cat_size))
    return model


class Encoder(nn.Module):
    def __init__(self, shape, dim_h, batch_norm, dropout, desired_nonlinearity, min_dim):
        super(Encoder, self).__init__()
        assert hasattr(nn, desired_nonlinearity), '%s is not a valid nonlinearity' % desired_nonlinearity
        nonlinearity = getattr(nn, desired_nonlinearity)()
        self.encoder = conv_encoder(shape, dim_h, batch_norm, dropout, nonlinearity, min_dim)

    def forward(self, x):
        return self.encoder(x)


if __name__ == '__main__':
    train_loader, test_loader = load_svhn('/Tmp/lavoiems', 32)
    shape = train_loader.dataset.data.shape
    encoder = Encoder(shape, 64, 100, True, None, 'ReLU', 2).cuda()
    for train_data in train_loader:
        inputs, labels = Variable(train_data[0].cuda()), Variable(train_data[1].cuda())
        print(encoder(inputs))
        exit(0)

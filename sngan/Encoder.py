import math
import torch.nn as nn
from torch.autograd import Variable
from SpectralNormLayer import SNConv2d, SNLinear

from loader import load_svhn
from modules import View, n_maps


def conv_encoder(shape, dim_h, o_size, batch_norm, nonlinearity, min_dim, Conv2d, Linear):
    model = nn.Sequential()
    n_convolution = int(math.log(shape[1] / min_dim, 2))
    f_size, stride, pad = 4, 2, 1
    for c in range(n_convolution + 1):
        n_maps_in = n_maps(c, dim_h, shape[0])
        n_maps_out = n_maps(c+1, dim_h, shape[0])
        conv = Conv2d(n_maps_in, n_maps_out, 3, 1, 1, bias=False)
        name = '3conv_%s_%s' % (n_maps_in, n_maps_out)
        model.add_module(name, conv)
        model.add_module('%s_%s' % (name, nonlinearity), nonlinearity)
        if c != n_convolution:
            conv = Conv2d(n_maps_out, n_maps_out, f_size, stride, pad, bias=False)
            name = '4conv_%s_%s' % (n_maps_out, n_maps_out)
            model.add_module(name, conv)
            model.add_module('%s_%s' % (name, nonlinearity), nonlinearity)
    cat_size = int(2 ** n_convolution * dim_h * (shape[1] / 2 ** n_convolution) * (shape[2] / (2 ** n_convolution)))
    model.add_module('flatten', View(-1, cat_size))
    model.add_module('lin', Linear(cat_size, o_size, bias=False))
    return model


class Encoder(nn.Module):
    def __init__(self, shape, dim_h, o_size, batch_norm, nonlinearity, min_dim):
        super(Encoder, self).__init__()
        self.encoder = conv_encoder(shape, dim_h, o_size, batch_norm, nonlinearity, min_dim, nn.Conv2d, nn.Linear)

    def forward(self, x):
        return self.encoder(x)


class SNEncoder(nn.Module):
    def __init__(self, shape, dim_h, o_size, batch_norm, nonlinearity, min_dim):
        super(SNEncoder, self).__init__()
        self.encoder = conv_encoder(shape, dim_h, o_size, batch_norm, nonlinearity, min_dim, SNConv2d, SNLinear)

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

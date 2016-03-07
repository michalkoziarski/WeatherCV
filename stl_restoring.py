from dnoise.cnn import Restoring
from dnoise.loaders import load_stl
from dnoise.noise import *


ds = load_stl(shape=(64, 64), grayscale=True, batch_size=1)
cnn = Restoring(input_shape=[64, 64, 1], output_shape=[42, 42, 1], weight_decay=0.)
cnn.train(ds, epochs=1000, noise=GaussianNoise(std=0.001), visualize=5, display_step=1000, learning_rate=0.001)

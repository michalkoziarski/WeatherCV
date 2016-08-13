import numpy as np
import matplotlib.pyplot as plt

from scipy import misc


class Image:
    def __init__(self, image=None, path=None, shape=None, keep_in_memory=True, preload=False, normalize=True,
                 noise=None, scale=(0, 255), grayscale=False):
        if preload and not keep_in_memory:
            raise ValueError('Can\'t preload without keeping in memory')

        if image is None and path is None:
            raise ValueError('Needs either image or path')

        self.path = path
        self.shape = shape
        self.keep_in_memory = keep_in_memory
        self.preload = preload
        self.normalize = normalize
        self.noise = noise
        self.scale = scale
        self.grayscale = grayscale
        self.image = None

        if preload or image is not None:
            self.load_and_process(image)

    def get(self):
        if self.image is not None:
            return self.image
        else:
            return self.load_and_process()

    def patch(self, size, coordinates=None):
        image = self.get()

        if coordinates:
            x, y = coordinates
        else:
            x = np.random.randint(image.shape[0] - size + 1)
            y = np.random.randint(image.shape[1] - size + 1)

        return image[x:(x + size), y:(y + size)]

    def load_and_process(self, image=None):
        if image is None:
            image = misc.imread(self.path)
        else:
            image = np.copy(image)

        if self.shape is not None:
            image = misc.imresize(image, self.shape)

            if self.normalize and self.scale[1] == 1.0:
                image = image / 255.

        if self.normalize and self.scale[1] == 255:
            if self.keep_in_memory:
                self.scale = (0.0, 1.0)

            image = image / 255.

        if self.grayscale and len(np.shape(image)) == 3 and np.shape(image)[2] >= 3:
            r, g, b = image[:, :, 0], image[:, :, 1], image[:, :, 2]

            image = 0.2989 * r + 0.5870 * g + 0.1140 * b

        if self.noise is not None:
            self.noise.set_scale(self.scale)

            image = self.noise.apply(image)

        if self.keep_in_memory:
            self.image = image

        return image

    def noisy(self, noise):
        return Image(image=self.image, path=self.path, shape=self.shape, keep_in_memory=True, normalize=self.normalize,
                     noise=noise, scale=self.scale, grayscale=self.grayscale)

    def display(self, path=None, size=None):
        image = self.get()

        if len(image.shape) == 3 and image.shape[2] == 1:
            image = np.squeeze(image, axis=(2,))

        color_map = plt.cm.Greys_r if len(image.shape) == 2 else None

        if size is not None:
            image = misc.imresize(image, size)

        if path is None:
            plt.imshow(image, cmap=color_map)
            plt.axis('off')
            plt.show()
        else:
            plt.imsave(path, image, cmap=color_map)


class Label:
    def __init__(self, label, one_hot=True, dictionary=None, length=None):
        if one_hot is True and dictionary is None and length is None:
            raise ValueError('If one_hot is true needs either dictionary or length')

        if one_hot:
            if dictionary is None:
                dictionary = range(length)

            if length is None:
                length = len(dictionary)

            self.label = np.zeros(length)
            self.label[dictionary.index(label)] = 1
        else:
            self.label = label

    def get(self):
        return self.label


class DataSet:
    def __init__(self, images, targets=None, batch_size=50):
        assert targets is None or len(images) == len(targets)

        self.images = images
        self.targets = targets
        self.batch_size = batch_size
        self.length = len(images)
        self.batches_completed = 0
        self.epochs_completed = 0
        self.current_index = 0

    def batch(self, size=None):
        if size is None:
            size = self.batch_size

        images, targets = self._create_batch(size)

        self.batches_completed += 1
        self.current_index += size

        if self.current_index >= self.length:
            self.current_index = 0
            self.epochs_completed += 1

            perm = np.random.permutation(self.length)

            self.images = self.images[perm]
            self.targets = self.targets[perm]

            epoch_completed = True
        else:
            epoch_completed = False

        return images, targets, epoch_completed

    def _create_batch(self, size):
        raise NotImplementedError


class LabeledDataSet(DataSet):
    def __init__(self, images, targets, batch_size=50):
        DataSet.__init__(self, images, targets, batch_size)

    def _create_batch(self, size):
        images = [image.get() for image in self.images[self.current_index:(self.current_index + size)]]
        targets = [target.get() for target in self.targets[self.current_index:(self.current_index + size)]]

        return np.array(images), np.array(targets)


class UnlabeledDataSet(DataSet):
    def __init__(self, images, noise=None, patch=None, batch_size=50):
        self.noise = noise
        self.patch = patch

        DataSet.__init__(self, images, batch_size=batch_size)

    def _create_batch(self, size):
        images = []
        targets = []

        for i in range(size):
            if self.current_index + i >= self.length:
                break

            target = self.images[self.current_index + i]

            if self.noise:
                image = target.noisy(self.noise)
            else:
                image = target

            if self.patch:
                x = np.random.randint(image.get().shape[0] - self.patch + 1)
                y = np.random.randint(image.get().shape[1] - self.patch + 1)

                image = image.patch(self.patch, coordinates=(x, y))
                target = target.patch(self.patch, coordinates=(x, y))
            else:
                image = image.get()
                target = target.get()

            images.append(image)
            targets.append(target)

        return np.array(images), np.array(targets)

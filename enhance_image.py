# Copyright 2019 The TensorFlow Hub Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


import os
import time
from PIL import Image
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import matplotlib.pyplot as plt
from pathlib import Path

os.environ["TFHUB_DOWNLOAD_PROGRESS"] = "True"

SAVED_MODEL_PATH = "https://tfhub.dev/captain-pool/esrgan-tf2/1"
model = hub.load(SAVED_MODEL_PATH)

class Enhance():

    def __init__(self, input_dir, output_dir, max_size_to_enhance=None):
        self.image_paths = [f"{input_dir}\\{file}" for file in os.listdir(input_dir) if os.path.isfile(f"{input_dir}\\{file}")]
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir) 
        self.max_size_to_enhance = max_size_to_enhance


    def preprocess_image(self, image_path):
        """ Loads image from path and preprocesses to make it model ready
            Args:
                image_path: Path to the image file
        """
        hr_image = tf.image.decode_image(tf.io.read_file(image_path))
        # If PNG, remove the alpha channel. The model only supports
        # images with 3 color channels.
        if hr_image.shape[-1] == 4:
            hr_image = hr_image[...,:-1]
        hr_size = (tf.convert_to_tensor(hr_image.shape[:-1]) // 4) * 4
        hr_image = tf.image.crop_to_bounding_box(hr_image, 0, 0, hr_size[0], hr_size[1])
        hr_image = tf.cast(hr_image, tf.float32)
        return tf.expand_dims(hr_image, 0)

    def save_image(self, image, file_name):
        """
        Saves unscaled Tensor Images.
        Args:
            image: 3D image tensor. [height, width, channels]
            file_name: Name of the file to save to.
        """
        if not isinstance(image, Image.Image):
            image = tf.clip_by_value(image, 0, 255)
            image = Image.fromarray(tf.cast(image, tf.uint8).numpy())
        image.save(f"{self.output_dir}\\{file_name}.jpg")
        print(f"Saved enhanced image as {file_name}.jpg")

    def plot_image(self, image, title=""):
        """
        Plots images from image tensors.
        Args:
            image: 3D image tensor. [height, width, channels].
            title: Title to display in the plot.
        """
        image = np.asarray(image)
        image = tf.clip_by_value(image, 0, 255)
        image = Image.fromarray(tf.cast(image, tf.uint8).numpy())
        plt.imshow(image)
        plt.axis("off")
        plt.title(title)

    def enhance_images(self):
        for image_path in self.image_paths:
            self.enhance_if_small(image_path)

    def enhance_if_small(self, image_path):
        """ Enhances image if it's small enough to enhance, otherwise just write the image to ourput_dir
        """
        if self.max_size_to_enhance is None: # enhance if no size restriction on enhancement
            self.enhance_image(image_path)

        else:
            # open image
            img = Image.open(image_path)
            w, h = img.size
            max_w, max_h = self.max_size_to_enhance
            if w <= max_w or h <= max_h: # enahnce if image is small enough
                self.enhance_image(image_path)
            else: # save existing image to new location
                file_name =  '.'.join(Path(image_path).name.split('.')[:-1]) # file name after removing the .jpg or other extension
                output_path = f"{self.output_dir}\\{file_name}.jpg"
                img.save(output_path, "jpeg")
                print(f"Saved as {file_name}.jpg")

    def enhance_image(self, image_path):
        file_name =  '.'.join(Path(image_path).name.split('.')[:-1]) # file name after removing the .jpg or other extension
        image = self.preprocess_image(image_path)
        enhanced_image = model(image)
        enhanced_image = tf.squeeze(enhanced_image)
        self.save_image(enhanced_image, file_name=file_name)




from skimage.segmentation import slic
from skimage.color import rgb2lab, deltaE_cie76
from scipy.spatial import KDTree
import requests
import numpy as np
import cv2
from sklearn.cluster import KMeans


def read_image_from_file_name(file_name):
    path = f"./coco/images/val2017/{file_name}"
    image = cv2.imread(path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def read_image_from_url(url):
    response = requests.get(url)
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


class DiversityHandler:
    def __init__(self):
        self.image_cache = {}

    def pixelate_image(self, image, pixel_size):
        """Pixelate the image."""
        height, width, _ = image.shape
        image_small = cv2.resize(
            image, (pixel_size, pixel_size), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(
            image_small, (width, height), interpolation=cv2.INTER_NEAREST)

    def extract_palette(self, image_obj, use_local_images=True, pixel_size=5, similarity_threshold=50, raw_image=None, apply_clustering=False, n_clusters=5):
        if raw_image is not None:
            image = raw_image
        elif use_local_images:
            if image_obj['file_name'] in self.image_cache:
                image = self.image_cache[image_obj['file_name']]
            else:
                image = read_image_from_file_name(image_obj['file_name'])
                self.image_cache[image_obj['file_name']] = image
        else:
            if image_obj['coco_url'] in self.image_cache:
                image = self.image_cache[image_obj['coco_url']]
            else:
                image = read_image_from_url(image_obj['coco_url'])
                self.image_cache[image_obj['coco_url']] = image

        pixelated_img = self.pixelate_image(image, pixel_size=pixel_size)

        # Convert image pixels to a set of unique colors
        potential_unique_colors = set(tuple(v)
                                      for v in pixelated_img.reshape(-1, 3))

        # Filter these colors using KDTree
        kd_tree = KDTree(np.array([[0, 0, 0]]))  # dummy initialization
        unique_colors = []
        for color in potential_unique_colors:
            if not kd_tree.query_ball_point(color, r=similarity_threshold):
                unique_colors.append(color)
                kd_tree = KDTree(np.array(unique_colors))

        if apply_clustering:
            # Adjust n_clusters based on the number of unique colors found
            n_clusters = min(n_clusters, len(unique_colors))

            kmeans = KMeans(n_clusters=n_clusters)
            kmeans.fit(np.array(unique_colors))
            cluster_centers = kmeans.cluster_centers_
            unique_colors = [tuple(map(int, center))
                             for center in cluster_centers]

        color_dominance = {color: 0 for color in unique_colors}
        kd_tree = KDTree(np.array(unique_colors))
        for color in pixelated_img.reshape(-1, 3):
            _, index = kd_tree.query(color)
            closest_color_tuple = unique_colors[index]
            color_dominance[closest_color_tuple] += 1

        total_pixels = pixel_size * pixel_size
        for color, count in color_dominance.items():
            color_dominance[color] = (count / total_pixels) * 100

        return [(color, color_dominance[color]) for color in unique_colors]

    def palettes_of_images(self, image_objs, use_local_images=True):
        return [self.extract_palette(img, use_local_images) for img in image_objs]

    def is_diverse_colors(self, image_objs, use_local_images=True, similarity_threshold=50):
        palette_list = self.palettes_of_images(
            image_objs, use_local_images=use_local_images)

        for i in range(len(palette_list)):
            for j in range(i+1, len(palette_list)):
                for color1, _ in palette_list[i]:
                    for color2, _ in palette_list[j]:
                        if self.color_similarity_lab(color1, color2) < similarity_threshold:
                            return False
        return True

    @staticmethod
    def color_similarity_lab(color1, color2):
        """Computes the similarity between two RGB colors using Lab color space."""
        color1_lab = rgb2lab(np.uint8(np.asarray([[color1]])))
        color2_lab = rgb2lab(np.uint8(np.asarray([[color2]])))
        return deltaE_cie76(color1_lab, color2_lab)

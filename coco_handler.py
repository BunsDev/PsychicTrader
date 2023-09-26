import io
from PIL import Image
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from pycocotools.coco import COCO
import json

import requests
from diversity_handler import DiversityHandler
from gpt_handler import JSON_OUTPUT_PROMPT, LIST_OUTPUT_PROMPT, GPTHandler, extract_data_from_json_response

# IMPORT QUANTUM RANDOM NUMBERS:
# a. In the get_random_image method:
# selected_img_id = random.choice(img_ids)
# Here, a random image ID is selected from the list of image IDs. This is a pseudo-random operation.

# b. In the get_random_images method:
# This method calls get_random_image in a loop, implying that the randomness in get_random_image is utilized multiple times here.
from quantum_random import QuantumRandom
random = QuantumRandom()

DIVERSITY_CHECK_PROMPT = """
Given a set of image captions, your task is to identify any that are too similar or not diverse enough in their descriptions. Diversity here refers to a broad representation of different scenes, objects, and activities. Redundant or overly similar captions can reduce the richness of the dataset and its usefulness for 
certain tasks.

The aim is to ensure that the final set of image captions represents a wide array of distinct visual scenarios. Captions that seem to describe similar scenes or objects should be flagged.

Task: Review the following list of image captions:

{captions}

Are all these captions diverse? If not, please identify the captions that are too similar or redundant and output ALL the captions TO-REMOVE (if n captions are similar, provide (n-1) captions TO-REMOVE). The goal is to maximize diversity in the image set. For good output: If diversity condition is satisfied, return {data_placeholder} (THIS IS SUPER IMPORTANT! Do not return `no` or `no captions` or the acceptable diverse list upond good output!). Follow ALL specified output formats!
"""


class CocoHandler:
    """
    A class to handle COCO dataset operations.
    Provides functionalities such as fetching random images and their captions.
    """

    def __init__(self, data_dir='./coco', data_type='val2017'):
        """
        Initialize the CocoHandler object.

        Parameters:
        - data_dir (str): Path to the directory containing the COCO data.
        - data_type (str): Specifies which subset of the COCO data to use (e.g., 'val2017', 'train2017').
        """
        self.data_dir = data_dir
        self.data_type = data_type
        # Construct the path to the annotation file
        self.ann_file = f'{self.data_dir}/annotations/captions_{self.data_type}.json'
        # Initialize the COCO API with the annotation file
        self.coco = COCO(self.ann_file)

    def get_random_image(self, excluded_images=None):
        """
        Fetches a random image and its associated captions from the COCO dataset, excluding images from the provided list.

        Parameters:
        - excluded_images (set): A set of image IDs to be excluded from the selection.

        Returns:
        - img (dict): A dictionary containing details of the randomly selected image.
        - captions (list): A list of captions associated with the selected image.
        """
        # Get a list of all image IDs in the dataset
        img_ids = self.coco.getImgIds()
        if excluded_images:
            img_ids = [
                img_id for img_id in img_ids if img_id not in excluded_images]
        # Randomly select an image ID
        selected_img_id = random.choice(img_ids)
        # Load the image details using the selected image ID
        img = self.coco.loadImgs(selected_img_id)[0]
        # Get annotation IDs associated with the selected image
        ann_ids = self.coco.getAnnIds(imgIds=selected_img_id)
        # Load the annotations using the annotation IDs
        anns = self.coco.loadAnns(ann_ids)
        # Extract captions from the annotations
        captions = [ann['caption'] for ann in anns]

        # Add color palette to the image object
        diversity_handler = DiversityHandler()
        color_palette = diversity_handler.extract_palette(img)
        img['color_palette'] = color_palette

        return img, captions

    def get_random_images(self, batch_size, excluded_images=None):
        """
        Fetches a batch of random images ensuring they are unique.

        Parameters:
        - batch_size (int): Number of images to retrieve.
        - excluded_images (set): A set of image IDs to be excluded from the selection.

        Returns:
        - list: List of unique image objects.
        """

        selected_images = []
        selected_captions = []

        while len(selected_images) < batch_size:
            image, caption = self.get_random_image(
                excluded_images=excluded_images)

            if image not in selected_images:
                selected_images.append(image)
                selected_captions.append(caption)

        return selected_images, selected_captions

    def get_diverse_image_set(self, n, max_attempts=50, buffer_multiplier=2, batch_size=10, use_local_images=True, debug=True, use_gpt=True, use_color=True, verbose=False):
        diversity_handler = DiversityHandler()
        gpt_handler = GPTHandler()

        selected_images = []
        selected_captions = []
        excluded_images = set()  # Keep track of images to be excluded

        attempts = 0

        while len(selected_images) < n and attempts < max_attempts:
            batch_images, batch_captions = self.get_random_images(
                batch_size, excluded_images=excluded_images)
            batch_captions = [captions[0] for captions in batch_captions]

            if use_color and (not diversity_handler.is_diverse_colors(batch_images, use_local_images=use_local_images)):
                attempts += 1
                continue

            if use_gpt:
                full_prompt = ''.join([DIVERSITY_CHECK_PROMPT.format(captions=json.dumps(
                    batch_captions), data_placeholder='{"data": []}'), LIST_OUTPUT_PROMPT, JSON_OUTPUT_PROMPT])
                response_raw = gpt_handler.get_response(full_prompt)
                response_data = extract_data_from_json_response(response_raw)

                if debug:
                    # Logging GPT raw response
                    print("GPT Response:", response_raw)

                if not response_data:
                    selected_images.extend(
                        batch_images[:n-len(selected_images)])
                    if debug:
                        print("All captions in the batch were found diverse.")
                else:
                    non_diverse_captions = response_data
                    for idx, caption in enumerate(batch_captions):
                        if caption not in non_diverse_captions and batch_images[idx] not in selected_images:
                            selected_images.append(batch_images[idx])
                            if debug:
                                print(
                                    f"Image {batch_images[idx]['id']} is selected.")
                        else:
                            # Add the image to the excluded set
                            excluded_images.add(batch_images[idx]['id'])
                            if debug:
                                print(
                                    f"Caption '{caption}' flagged as non-diverse by GPT.")

                        if len(selected_images) == n:
                            break

                attempts += 1

        # Validation to ensure non-diverse captions flagged by GPT aren't in the final selection
        for image in selected_images:
            ann_ids = self.coco.getAnnIds(imgIds=image['id'])
            anns = self.coco.loadAnns(ann_ids)
            image_captions = [ann['caption'] for ann in anns]
            for cap in image_captions:
                # Assert that none of the flagged captions are in the final selection
                assert cap not in non_diverse_captions, f"Caption '{cap}' was flagged as non-diverse but still present in the final selection."
                if verbose:
                    print(
                        f"Validated image {image['id']}: No non-diverse captions found.")

        if len(selected_images) < n:
            raise Exception(
                "Failed to find a diverse set of images after max attempts.")

        return selected_images


def display_image_with_colors(image_details, captions):
    print(f"image_details: {image_details}\n captions: {captions}")

    # Load the image from the provided URL
    response = requests.get(image_details['coco_url'])
    image = Image.open(io.BytesIO(response.content))
    image = np.array(image)

    # Create a new figure
    fig, ax = plt.subplots(1, 2, figsize=(15, 7))

    # Display the image on the left
    ax[0].imshow(image)
    ax[0].axis('off')
    ax[0].set_title("Image")

    # Display the color palette on the right
    num_colors = len(image_details['color_palette'])
    for idx, (color, dominance) in enumerate(image_details['color_palette']):
        normalized_color = tuple([x/255 for x in color])
        rect = patches.Rectangle(
            (0, idx/num_colors), 1, 1/num_colors, linewidth=0, edgecolor='none', facecolor=normalized_color)

        ax[1].add_patch(rect)
    ax[1].axis('off')
    ax[1].set_title("Color Palette")

    # Display the caption below the image
    caption_text = " ".join(captions)
    plt.figtext(0.5, -0.1, caption_text, wrap=True,
                horizontalalignment='center', fontsize=12)

    plt.tight_layout()
    plt.show()


# # Test the function
# handler = CocoHandler()
# img, captions = handler.get_random_image()
# display_image_with_colors(img, captions)

# # Example usage
# handler = CocoHandler()
# img, captions = handler.get_random_image()
# print("Image Details:", img)
# print("Captions:", captions)

# images = handler.get_diverse_image_set(6, verbose=True)
# print(images)

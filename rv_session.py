import random
from coco_handler import CocoHandler
from crypto_handler import CryptoHandler
from gpt_handler import GPTHandler, JSON_OUTPUT_PROMPT, LIST_OUTPUT_PROMPT, extract_data_from_json_response


class RVSession:
    """
    1. The user initiates an ARV session by selecting a 'start time' slightly in the future, and an 'end time' beyond that.
    2. The user is then prompted to describe an image they foresee at the 'end time'. This image will correspond to the top-performing cryptocurrency between the 'start time' and 'end time'.
    3. The user's description is compared to a set of pre-selected images from the COCO dataset, each associated with different cryptocurrencies. The closest matching image determines the crypto prediction.
    4. A buy order for the predicted crypto is placed immediately.
    5. At the 'end time', a sell order for the crypto is executed.
    6. Simultaneously at the 'end time', the system reveals the actual top-performing crypto's associated image to the user. This is the image the user was supposed to 'see' during their initial RV session.
    7. The process revolves around the principle that the user, during their RV session, is psychically viewing this 'end time' image.

    It's vital to note that the associated image for the top-performing crypto is ONLY known at the 'end time'. Before this point, it remains undisclosed.
    """

    def __init__(self, all_trading_pairs: list[str], coco_handler: CocoHandler, crypto_handler: CryptoHandler, gpt_handler: GPTHandler):
        self.all_trading_pairs = all_trading_pairs
        self.coco_handler = coco_handler
        self.crypto_handler = crypto_handler
        self.gpt_handler = gpt_handler
        self.buy_time = None
        self.sell_time = None
        self.user_description = None
        self.matched_crypto = None
        # Mapping between cryptos and their associated images
        self.crypto_image_map = {}
        self.n_cryptos = None
        # the n randomly-sampled cryptos from all_trading_pairs
        self.sampled_cryptos = None

    def start_session(self, n_cryptos: int):
        """
        Initiates the ARV session by associating random images from the COCO dataset
        with different cryptocurrencies.
        """
        self.n_cryptos = n_cryptos
        # Sample n_cryptos from the crypto_list
        self.sampled_cryptos = random.sample(self.all_trading_pairs, n_cryptos)

        # Fetch n_cryptos diverse images and their captions
        diverse_image_set = self.coco_handler.get_diverse_image_set(
            n=self.n_cryptos)

        # Create a dictionary that maps each cryptocurrency to its associated image object
        self.crypto_image_map = {}
        for crypto, img in zip(self.sampled_cryptos, diverse_image_set):
            ann_ids = self.coco_handler.coco.getAnnIds(imgIds=img['id'])
            anns = self.coco_handler.coco.loadAnns(ann_ids)
            captions = [ann['caption'] for ann in anns]
            self.crypto_image_map[crypto] = {
                "url": img['coco_url'],
                "caption_list": captions,
                "dominant_colors": img["dominant_colors"]
            }

        # communicate to cryptohandler (wraps freqtradehandler) to start communicating (and receiving data) with strategy
        self.crypto_handler.start_session(crypto_pairs=self.sampled_cryptos)

    def reset_session(self):
        # clear files for communicating to cryptohandler (wraps freqtradehandler)

        self.crypto_handler.reset_session()

    def get_crypto_caption_map(self):
        """
        Extracts captions from the crypto_image_map and returns a mapping between 
        cryptocurrencies and their associated image captions.
        """
        crypto_caption_map = {}
        for crypto, img_data in self.crypto_image_map.items():
            # Taking all captions for each image
            crypto_caption_map[crypto] = img_data['caption_list']

        return crypto_caption_map

    def set_buy_sell_times(self, buy_time, sell_time):
        self.buy_time = buy_time
        self.sell_time = sell_time

    def record_rv_session(self, description):
        self.user_description = description

    def image_match(self, n_matches=1, debug=True):
        if debug:
            print("User Description:", self.user_description)
            print("Crypto Image Map:", self.crypto_image_map)
            print("Number of Matches:", n_matches)

        IMAGE_MATCH_PROMPT = """
        Given a user's detailed description of an image, your task is to match this description against a list of image captions. The user's description, labeled 'user_description', is a vivid account that could encompass visual aspects, feelings, symbols, and other multi-sensory perceptions. In contrast, the 'image_captions' list contains succinct descriptions of the primary objects and activities in various images without delving into specific details. 

        While the user's description might include richer details like colors, emotions, and background activities, the image captions will be more generic. To match them effectively, you'll need to envision the scenes depicted by the image captions, filling in the gaps with potential details that the user_description might be referencing. 

        Your goal is two-fold:
        1. Score each caption in 'image_captions' for similarity against 'user_description' in a range from 0% (no match) to 100% (perfect match).
        2. Sort these scores in descending order and return the top 'n_matches' as the best matching captions.

        Task: Using the following parameters:

        user_description: {user_description}
        image_captions: {image_captions}
        n_matches: {n_matches}

        Please provide the SYMBOLS (keys/names) of the best-matching image captions based on the above guidelines. DO NOT provide me the captions themselves!

        """.format(user_description=self.user_description, image_captions=self.get_crypto_caption_map(), n_matches=n_matches)

        full_prompt = ''.join(
            [IMAGE_MATCH_PROMPT, LIST_OUTPUT_PROMPT, JSON_OUTPUT_PROMPT])

        if debug:
            print("Full Prompt to GPT:", full_prompt)

        matched_captions_response = self.gpt_handler.get_response(full_prompt)

        if debug:
            print("GPT Response:", matched_captions_response)

        matched_captions = extract_data_from_json_response(
            matched_captions_response)

        if debug:
            print("Extracted matched_captions:", matched_captions)

        self.matched_crypto = matched_captions[0]  # top prediction

        # uppercase, gpt output is always lowercased
        self.matched_crypto = self.matched_crypto.upper()

        if debug:
            print("Matched Crypto:", self.matched_crypto)

        return self.matched_crypto

    def buy_matched_crypto(self):
        symbol = self.matched_crypto
        amount = 1
        self.crypto_handler.place_buy_order(symbol, amount)

    def sell_matched_crypto(self):
        symbol = self.matched_crypto
        amount = 1
        self.crypto_handler.place_sell_order(symbol, amount)

    def get_associated_image(self, crypto_symbol):
        # Fetch the image associated with the given crypto_symbol from our mapping
        return self.crypto_image_map.get(crypto_symbol)

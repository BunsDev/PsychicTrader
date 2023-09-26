import re
import json
import g4f
import requests

JSON_OUTPUT_PROMPT = """Please respond in the following exact format: { \"data\": \"YOUR RESPONSE HERE\" }. Do not change the structure, capitalization, or formatting. DO NOT include any for-human-user text or comments, you are communicating with a computer software program via specified format ONLY! If using in with other formatting like lists, dicts,obj, literals, strings, etc. always set it as the value to the "data" key!"""

LIST_OUTPUT_PROMPT = "Provide your response as a comma-separated list. Include the list brackets `[]` surrounding your list! (ex. [`'a`', 2]). Strictly follow the format. "


def extract_data_from_json_response(response_text):
    # Use regex to extract the { "data": ... } pattern from the response
    match = re.search(r'{\s*"data"\s*:\s*(.+?)}', response_text)

    if not match:
        raise ValueError(f"'data' object not found in: {response_text}")

    try:
        # Extract the matched JSON object and parse it
        data_json_str = match.group(0)
        data_json = json.loads(data_json_str)

        # Extract the 'data' key's value
        data_val = data_json['data']

        # If it's a string representation of a list or object, clean and parse
        if isinstance(data_val, str) and (data_val.startswith('[') and data_val.endswith(']') or
                                          data_val.startswith('{') and data_val.endswith('}')):
            # Replace single quotes with double quotes
            data_val = data_val.replace("'", '"')
            # Remove backticks
            data_val = data_val.replace("`", "")
            return json.loads(data_val)

        return data_val

    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(
            f"Error parsing extracted data: {data_json_str}. Error: {e}")

    return None


class GPTHandler:

    def __init__(self, model=g4f.models.gpt_4, provider=g4f.Provider.Bing):
        self.model = model
        self.provider = provider
        self.working_gpt4_providers = [
            g4f.Provider.Aivvm,
            g4f.Provider.DeepAi,
            g4f.Provider.Bing,
            g4f.Provider.ChatBase,
            g4f.Provider.Raycast,
            g4f.Provider.Liaobots
        ]

    def get_response(self, prompt):

        response_stream = g4f.ChatCompletion.create(
            model=self.model,
            provider=self.provider,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            # for Bing (WORKS WITH BLANK COOKIES)
            cookies={"cookie_name": "value", "cookie_name2": "value2"},
            auth=True
        )

        # Collecting messages
        messages = []
        for message in response_stream:
            # Removing leading newlines
            messages.append(message.lstrip("\n"))

        # Joining the messages to get a full response
        return ''.join(messages)

    def test_providers(self, providers):
        """
        Test a list of providers to check which ones respond correctly to a long prompt.

        Parameters:
        - providers (list): A list of provider constants to test.

        Returns:
        - list: A list of working providers sorted by their output message length.
        """
        working_providers = []

        # A long and detailed prompt to test maximum input length and detailed task.
        # Assuming 2048 is the maximum input length for most providers.
        prompt = "A" * 1048
        prompt += """
        Given the detailed history of cryptography, from the early Caesar cipher, through the World War II Enigma machine, 
        to modern-day RSA and Elliptic Curve Cryptography, provide a detailed analysis on how quantum computers might pose 
        a threat to current cryptographic standards and detail potential post-quantum cryptographic solutions. 
        Your response should be exhaustive and detailed, covering every aspect of the question in depth.
        """

        for provider in providers:
            try:
                response = self.get_response(prompt, provider)
                response_data = extract_data_from_json_response(response)

                # Check if the provider's response contains the expected output.
                if response_data:
                    working_providers.append(
                        (provider, len(response_data)))
                    print(
                        f"Provider {provider} responded with message length: {len(response_data)}")
            except Exception as e:
                print(f"Error testing provider {provider}: {e}")

        # Sort the working providers by the length of their output message.
        working_providers.sort(key=lambda x: x[1], reverse=True)

        return [provider[0] for provider in working_providers]


# # # Example Usage
# handler = GPTHandler()
# # response = handler.get_response("HELLO")
# # print(response)
# print(handler.test_providers(handler.working_gpt4_providers))

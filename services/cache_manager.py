import json
import os
import logging


class NotionCache:
    def __init__(self, cache_file="cache/notion_cache.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
                    else:
                        logging.warning(
                            f"Cache file {self.cache_file} is empty. Initializing with an empty dictionary."
                        )
                        return {}
            except json.JSONDecodeError:
                logging.error(
                    f"Error decoding JSON from {self.cache_file}. Initializing with an empty dictionary."
                )
                return {}
        else:
            logging.info(
                f"Cache file {self.cache_file} does not exist. Initializing with an empty dictionary."
            )
            return {}

    def save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def add_to_cache(self, data):
        for item in data:
            key = item["properties"]["Name"]["title"][0]["text"]["content"]
            self.cache[key] = item
        self.save_cache()

    def filter_with_cache(self, data):
        new_data = []
        for item in data:
            key = item["properties"]["Name"]["title"][0]["text"]["content"]
            if key not in self.cache:
                new_data.append(item)

        if new_data:
            self.add_to_cache(new_data)

        return new_data if new_data else None

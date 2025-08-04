import re
import json
import time
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.google_auth import Authenticator


class ClassroomDataManager:
    SCOPES = ["https://mail.google.com/#search/new+assignment"]

    def __init__(self, credentials_file="credentials.json", token_file="token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None

    def save_to_json(self, data, filename):
        # if the data type is a list, we need to convert it to a dictionary
        print(f"Saving data to {filename}...")
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")

    def authenticate(self):
        auth = Authenticator(self.credentials_file)
        self.creds = auth.get_credentials()
        if not self.creds:
            print("No valid credentials found.")
            self.creds = auth.create_token()
        return self.creds

    def get_messages(self, max_results=100):
        print(f"Fetching up to {max_results} messages...")
        # Search query to get only classroom assignment emails after 8/1/25 (recent)
        query = 'from:no-reply@classroom.google.com subject:"New assignment:" after:2025/6/1'
        
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", maxResults=max_results, q=query)
                .execute()
            )
            messages = results.get("messages", [])
            print(f"Fetched {len(messages)} classroom assignment messages.")

            # Save fetched messages

            return messages
        except HttpError as error:
            print(f"An error occurred while fetching messages: {error}")
            return []

    def get_message_details(self, message_id, max_retries=3, retry_delay=5):
        print(f"Fetching details for message ID: {message_id}")
        for attempt in range(max_retries):
            try:
                message = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message_id)
                    .execute()
                )
                print(f"Successfully fetched details for message ID: {message_id}")
                return message
            except TimeoutError:
                if attempt < max_retries - 1:
                    print(
                        f"Timeout error occurred. Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                else:
                    print(
                        f"Failed to fetch details for message ID: {message_id} after {max_retries} attempts."
                    )
                    return None
            except HttpError as error:
                print(f"An error occurred while fetching message details: {error}")
                return None

    def decode_body(self, body):
        return base64.urlsafe_b64decode(body).decode("utf-8")

    def process_payload(self, payload):
        headers = {
            header["name"].lower(): header["value"]
            for header in payload.get("headers", [])
        }
        body = self.decode_body(payload.get("body", {}).get("data", ""))

        processed_payload = {
            "headers": headers,
            "body": body,
            "mimeType": payload.get("mimeType", ""),
            "filename": payload.get("filename", ""),
            "parts": [self.process_payload(part) for part in payload.get("parts", [])],
        }
        return processed_payload

    def filter_messages(self, messages):
        """
        Filter a list of messages based on the given criteria.

        :param messages: The list of messages to filter
        :return: A list of messages that meet all criteria
        """
        filtered_messages = []

        for message in messages:
            headers = message["payload"]["headers"]
            from_header = headers.get("from", "").lower()
            subject_header = headers.get("subject", "").lower()
            if (
                "classroom.google.com" in from_header
                and "new assignment" in subject_header
            ):
                filtered_messages.append(message)

        return filtered_messages

    def process_messages(self, max_results=100, filter_criteria=None):
        messages = self.get_messages(max_results)
        print(f"Total messages fetched: {len(messages)}")

        processed_messages = []
        for message in messages:
            details = self.get_message_details(message["id"])
            if details:
                message = {
                    "id": details["id"],
                    "threadId": details["threadId"],
                    "labelIds": details.get("labelIds", []),
                    "snippet": details.get("snippet", ""),
                    "payload": self.process_payload(details.get("payload", {})),
                }
            else:
                print(f"Could not fetch details for message ID: {message['id']}")

        print(f"Total processed messages: {len(processed_messages)}")

        return processed_messages

    def filter_message(self, message, criteria):
        """
        Filter a message based on the given criteria.

        :param message: The message to filter
        :param criteria: A dictionary of criteria to filter by
        :return: True if the message meets all criteria, False otherwise
        """
        for key, value in criteria.items():
            if key == "from":
                from_header = next(
                    (
                        header["value"]
                        for header in message["payload"]["headers"]
                        if header["name"].lower() == "from"
                    ),
                    "",
                )
                if value.lower() not in from_header.lower():
                    return False
            elif key == "subject":
                subject_header = next(
                    (
                        header["value"]
                        for header in message["payload"]["headers"]
                        if header["name"].lower() == "subject"
                    ),
                    "",
                )
                if value.lower() not in subject_header.lower():
                    return False
            elif key == "label":
                if value not in message.get("labelIds", []):
                    return False
            # Add more criteria as needed
        return True

    # def filter_messages(self, messages):
    #     """
    #     Filter a list of messages based on the given criteria.

    #     :param messages: The list of messages to filter
    #     :param criteria: A dictionary where keys are header names and values are desired header values
    #     :return: A list of messages that meet all criteria
    #     """
    #     filtered_messages = []

    #     for message in messages:
    #         if "classroom.google.com" in message['payload']['headers']['From'] and "New assignment" in message['payload']['headers']['Subject']:
    #             filtered_messages.append(message)

    #     return filtered_messages

    def process_messages(self, max_results=100, filter_criteria=None):
        messages = self.get_messages(max_results)
        print(f"Total messages fetched: {len(messages)}")

        processed_messages = []
        for message in messages:
            details = self.get_message_details(message["id"])
            if details:
                message = {
                    "id": details["id"],
                    "threadId": details["threadId"],
                    "labelIds": details.get("labelIds", []),
                    "snippet": details.get("snippet", ""),
                    "payload": self.process_payload(details.get("payload", {})),
                }
                processed_messages.append(message)
            else:
                print(f"Could not fetch details for message ID: {message['id']}")

        print(f"Total processed messages: {len(processed_messages)}")

        return processed_messages

    def parse_message_content(self, messages):
        content = []
        for message in messages:
            return None

    def extract_assignment_info(self, messages):
        extracted_data = []
        for data in messages:
            # Extract the HTML content
            html_content = data["payload"]["parts"][1]["body"]

            # Extract assignment name
            assignment_name_match = re.search(r"<div>(.*?)</div>", html_content)
            assignment_name = (
                assignment_name_match.group(1) if assignment_name_match else "Not found"
            )

            # Extract class link

            link_pattern = r"https://accounts\.google\.com/AccountChooser\?continue="
            link_match = re.search(
                r"href=(https://accounts\.google\.com/AccountChooser\?continue=https://classroom\.google\.com/c/[^&]+)",
                html_content,
            )
            class_link = link_match.group(1) if link_match else "Not found"
            class_link = re.sub(link_pattern, "", class_link)

            assignment_match = re.search(
                r"href=(https://accounts\.google\.com/AccountChooser\?continue=https://classroom\.google\.com/c/[^&]+/a/[^&]+)",
                html_content,
            )
            assignment_link = (
                assignment_match.group(1) if assignment_match else "Not found"
            )
            assignment_link = re.sub(link_pattern, "", assignment_link)

            # Extract assignment description
            description_match = re.search(r"<ul>(.*?)</ul>", html_content, re.DOTALL)
            if description_match:
                description_items = re.findall(
                    r"<li>(.*?)</li>", description_match.group(1)
                )
                assignment_description = "\n".join(description_items)
            else:
                assignment_description = "Not found"

            # Extract class name
            class_match = re.search(
                r">([^<]+)</td></tr></table></a></td>", html_content
            )
            class_name = class_match.group(1) if class_match else "Not found"

            # Extract due date
            due_date_match = re.search(r"Due ([^<]+)", html_content)
            due_date = due_date_match.group(1) if due_date_match else "Not found"

            # Extract posted date and author
            posted_info_match = re.search(r"Posted on ([^<]+) by ([^<]+)", html_content)
            if posted_info_match:
                posted_date = posted_info_match.group(1)
                posted_by = posted_info_match.group(2)
            else:
                posted_date = "Not found"
                posted_by = "Not found"

            extracted_data.append(
                {
                    "assignment_name": assignment_name,
                    "assignment_link": assignment_link,
                    "class_link": class_link,
                    "assignment_description": assignment_description,
                    "class_name": class_name,
                    "due_date": due_date,
                    "posted_date": posted_date,
                    "posted_by": posted_by,
                }
            )
        return extracted_data

    def run(
        self, max_results=100, output_file="classroom_data.json", filter_criteria=None
    ):
        print("Starting ClassroomDataManager...")
        self.authenticate()
        self.service = build("gmail", "v1", credentials=self.creds)
        processed_messages = self.process_messages(max_results, filter_criteria)
        # print(processed_messages)
        if processed_messages:
            # self.save_to_json(processed_messages, output_file)
            print(f"Processed {len(processed_messages)} messages.")
            return processed_messages
        else:
            print("No messages were processed. Check the logs for errors.")
            return None

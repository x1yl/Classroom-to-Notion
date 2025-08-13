import os
import json
import logging
import pathlib
import sys
from dotenv import load_dotenv
from services.classroom import ClassroomDataManager
from services.notion import NotionDatabaseManager
from services.assignment_parser import AssignmentParser
from services.cache_manager import NotionCache

# Set up logging: default to stdout (serverless-friendly). Optional file logging via env.
log_to_file = os.getenv("LOG_TO_FILE", "false").lower() in ("1", "true", "yes")
handlers = []
if log_to_file:
    log_path = os.getenv("LOG_FILE_PATH", "classroom_to_notion.log")
    try:
        # Ensure parent dir exists when path has dirs
        parent = pathlib.Path(log_path).parent
        if str(parent) not in (".", ""):
            parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        handlers.append(file_handler)
    except Exception:
        # Fall back to stdout if file is not writable
        handlers.append(logging.StreamHandler(sys.stdout))
else:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers,
)


def load_json_file(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read().strip()
            if content:
                return json.loads(content)
            else:
                logging.warning(f"File {file_path} is empty. Returning an empty list.")
                return []
    except FileNotFoundError:
        logging.info(f"File {file_path} not found. Returning an empty list.")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. Returning an empty list.")
        return []


def main(after_date=None):
    try:
        # If no date provided as parameter, check command line argument
        if after_date is None and len(sys.argv) > 1:
            after_date = sys.argv[1]
            print(f"Using date filter: after:{after_date}")
        elif after_date is not None:
            print(f"Using date filter: after:{after_date}")
        else:
            print("No date specified, using yesterday's date as default")
            print("To specify a date, run: python main.py YYYY/MM/DD")
            print("Example: python main.py 2025/8/1")

        load_dotenv()
        cdm = ClassroomDataManager()
        ndm = NotionDatabaseManager(
            database_id=os.environ.get("NOTION_DATABASE_ID"),
            token=os.environ.get("NOTION_TOKEN"),
        )
        notion_cache = NotionCache()

        # Initialize AssignmentParser
        ap = AssignmentParser()

        # Use lowercase keys for filter criteria
        filter_criteria = {
            "from": "no-reply@classroom.google.com",
            "subject": "New assignment",
        }

        email_cache = load_json_file("outputs/classroom_data.json")

        # Improved caching logic
        if len(email_cache) == 0:
            logging.info("Cache is empty, running service")
            messages = cdm.run(after_date=after_date, filter_criteria=filter_criteria)
        else:
            # Check latest messages to see if there are any new ones
            latest_messages = cdm.run(
                after_date=after_date, filter_criteria=filter_criteria
            )
            if latest_messages:
                # Check if any of the new messages are not in our cache
                cached_ids = {msg["id"] for msg in email_cache}
                new_message_exists = any(
                    msg["id"] not in cached_ids for msg in latest_messages
                )

                if not new_message_exists:
                    logging.info("No new messages. Using email_cache for data")
                    messages = email_cache
                else:
                    messages = latest_messages
                    logging.info(f"Retrieved {len(messages)} messages")
            else:
                messages = email_cache  # Fallback to cache if API call fails

        # Save the messages to cache
        if messages:
            cdm.save_to_json(messages, "outputs/classroom_data.json")

            filtered_messages = cdm.filter_messages(messages)
            cdm.save_to_json(filtered_messages, "outputs/filtered_classroom_data.json")

            # Extract assignment info (messages are already filtered)
            print("filtering messages")
            extracted_data = cdm.extract_assignment_info(filtered_messages)
            if extracted_data:
                cdm.save_to_json(
                    extracted_data, "outputs/extracted_classroom_data.json"
                )

                # Parse and filter
                parsed_data = ap.parse_assignments(extracted_data)
                uncached_data = notion_cache.filter_with_cache(parsed_data)

                # Add new assignments to Notion
                if not uncached_data:
                    logging.info("No new assignments to process")
                    print("No new assignments to process")
                    print("-------------------------------------------------")
                    return {"message": "No new assignments to process"}
                else:
                    print(
                        f"Adding {len(uncached_data)} new assignments to Notion database..."
                    )
                    for i, assignment in enumerate(uncached_data, 1):
                        assignment_name = assignment["properties"]["Name"]["title"][0][
                            "text"
                        ]["content"]
                        print(f"  {i}. Adding: {assignment_name}")

                    responses = ndm.post_data(uncached_data)

                    # Check responses and print results
                    successful_additions = 0
                    failed_additions = 0
                    for i, response in enumerate(responses):
                        assignment_name = uncached_data[i]["properties"]["Name"][
                            "title"
                        ][0]["text"]["content"]
                        if (
                            isinstance(response, dict)
                            and response.get("object") == "page"
                        ):
                            successful_additions += 1
                            print(f"  ✓ Successfully added: {assignment_name}")
                        else:
                            failed_additions += 1
                            print(f"  ✗ Failed to add: {assignment_name}")
                            if isinstance(response, dict) and "message" in response:
                                print(f"    Error: {response['message']}")

                    print(
                        f"\nSummary: {successful_additions} successful, {failed_additions} failed"
                    )
                    logging.info(
                        f"Processed {len(responses)} new assignments: {successful_additions} successful, {failed_additions} failed"
                    )
                    logging.info("Saving assignment responses to file")
                    cdm.save_to_json(responses, "outputs/new_assignments.json")
                    print("-------------------------------------------------")
                    return {
                        "message": f"Processed {len(responses)} new assignments: {successful_additions} successful, {failed_additions} failed"
                    }
            else:
                logging.warning("No assignments extracted from messages")
                return {"message": "No assignments extracted from messages"}
        else:
            logging.warning("No messages retrieved")
            return {"message": "No messages retrieved"}

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        print(e)
        return {"message": f"Error: {str(e)}"}


if __name__ == "__main__":
    main()

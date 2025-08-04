# Classroom to Notion

Classroom to Notion is an automation tool that integrates Google Classroom assignments (via Gmail) with Notion tasks using AI-powered parsing and matching.

## Features

- Fetch Classroom assignments from Gmail
- Retrieve existing activities from Notion
- AI-powered matching of assignments to activities
- Automatic creation of Notion tasks based on Classroom assignments
- Flexible parsing of different assignment formats

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- A Notion account with API access
- A Google account with Gmail API enabled

## Installation

1. Clone the repository:

```
git clone https://github.com/varadanvk/Classroom-to-Notion.git
cd Classroom-to-Notion
```

2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Set up Notion Integration:

- Go to [Notion Integrations](https://www.notion.so/my-integrations) and create a new integration
- Note down the API key provided
- Share your Notion databases with the integration
- For more details, check out [Notion's guide on creating integrations](https://developers.notion.com/docs/create-a-notion-integration)
- This is the [Task Database Schema](https://varadankalkunte.notion.site/e24d5164b78a417a95515759ccc31663?v=ef26c66dc99f4579999ccdaaed801e80&pvs=4) you can use as a reference

4. Set up Gmail API:

- Follow the [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python) to:
  - Enable the Gmail API
  - Download your `credentials.json` file
- Place the `credentials.json` file in the project root

5. Set up your environment variables:

- Create a `.env` file in the project root
- Add the following variables:

  ```
  NOTION_TOKEN=your_notion_api_token
  NOTION_DATABASE_ID=your_notion_tasks_database_id
  CALENDAR_ACCOUNT=your_gmail_account
  ```

Note: If your school email doesn't allow access to Google Developers, set up email forwarding to a personal email address that you can use for API access.

## Usage

1. Find your Notion database ID:

- Open your Notion database
- The ID is in the URL: https://www.notion.so/username/DATABASE_ID?v=...
- Copy the DATABASE_ID part 

2. Update the `NOTION_DATABASE_ID` in your `.env` file with this ID

3. Make sure your Notion database has the following properties:
   - Name (Title)
   - Category (Select)
   - Course (Text)
   - Date Span (Date)
   - Due (Date)
   - Last edited (Date)
   - Points (Number)
   - Reminder (Date)
   - Status (Select)
   - URL (URL)

4. Run the main script:

```
python main.py
```

This will prompt you to input your teacher's name for each activity. Once that is finished, all your activity relations will be added in.

5. Run the scheduelr script:

```
python scheduler.py
```

4. The script will:

- Fetch Classroom assignment emails from your Gmail
- Retrieve activities from your Notion database
- Match assignments to activities
- Create new tasks in Notion for the assignments

## Project Structure

- `main.py`: The entry point of the application
- `services/`:
  - `classroom.py`: Handles interaction with the Gmail API to fetch Classroom assignments
  - `notion.py`: Manages Notion API operations
  - `assignment_parser.py`: Contains the parsing and matching logic
  - `cache_manager.py`: Manages caching of processed assignments

## Contributing

Contributions to the Classroom to Notion project are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- Notion for their API
- Google for the Gmail API

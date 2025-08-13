# Classroom to Notion

Classroom to Notion is an automation tool that fetches Google Classroom assignments from Gmail and automatically creates tasks in your Notion database.

## Features

- Fetch Google Classroom assignment emails from Gmail
- Parse assignment details (name, due date, course, etc.)
- Automatically create Notion tasks for new assignments
- Cache management to avoid duplicate entries
- Timezone support (uses system timezone)

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- A Notion account with API access
- A Google account with Gmail API enabled

## Installation

1. Clone the repository:

```
git clone https://github.com/x1yl/Classroom-to-Notion.git
cd Classroom-to-Notion
```

2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Set up Notion Integration:

- Go to [Notion Integrations](https://www.notion.so/my-integrations) and create a new integration
- Note down the API key provided
- Share your Notion database with the integration
- For more details, check out [Notion's guide on creating integrations](https://developers.notion.com/docs/create-a-notion-integration)
- You can use this [Notion Database Template](https://classroom-template.notion.site/24583b2b4d1280ba958ddd237a5679c3?v=24583b2b4d128172b330000cbe9042de) as a starting point

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
  NOTION_DATABASE_ID=your_notion_database_id
  CALENDAR_ACCOUNT=your_gmail_account
  API_SECRET=your-secure-api-key-here
  API_URL=http://localhost:8888

  #optional variables
  TOKEN_EARLY_REFRESH_MINUTES=10
  TOKEN_MAX_AGE_DAYS=7
  TOKEN_FORCE_REAUTH_ON_MAX_AGE=true
  ```

**Important**: Generate a strong, random API secret for server authentication. This protects your API endpoints from unauthorized access.

Note: If your school email doesn't allow access to Google Developers, set up email forwarding to a personal email address that you can use for API access.

## Usage

1. Find your Notion database ID:

- Open your Notion database
- The ID is in the URL: https://www.notion.so/username/DATABASE_ID?v=...
- Copy the DATABASE_ID part

2. Update the `NOTION_DATABASE_ID` in your `.env` file with this ID

3. Make sure your Notion database has the following properties (or use the template above):

   - Name (Title)
   - Category (Select)
   - Course (Select)
   - Date Span (Date)
   - Due (Date)
   - Last edited (Date)
   - Points (Number)
   - Reminder (Date)
   - Status (Status)
   - URL (URL)

4. Run the setup script to create necessary directories:

```
python setup.py
```

5. Run the main script:

```
python main.py
```

Or specify a custom date to fetch assignments from:

```
python main.py 2025/8/1
```

6. The script will:

- Fetch Google Classroom assignment emails from your Gmail (after the specified date)
- Parse assignment details from the emails
- Check for new assignments not already in your database
- Create new tasks in Notion for any new assignments found

## Date Parameters

By default, the script fetches assignments from the day before today onwards. You can specify a different starting date:

- **Yesterday (default)**: `python main.py`
- **Custom date**: `python main.py 2025/7/15` (gets assignments after July 15, 2025)
- **Date format**: Use `YYYY/MM/DD` format (e.g., `2025/8/1` for August 1, 2025)

## Web Server

To run the sync as a web server with API endpoints:

```
python run_server.py
```

The server runs on `http://localhost:8888` and provides these endpoints:

### API Endpoints:

- **GET /** - Server status check (no auth required)
- **POST /run-sync** - Run sync and wait for results (requires auth)
- **POST /trigger-sync** - Start sync in background (requires auth)
- **POST /test** - Test endpoint (requires auth)
- **GET /health** - Health check (no auth required)

### Authentication:

All sync endpoints require Bearer token authentication. Include your API secret in the Authorization header:

```bash
# Set your API secret
export API_SECRET="your-secure-api-key-here"

# Default (yesterday's date) with authentication
curl -X POST "http://localhost:8888/run-sync" \
  -H "Authorization: Bearer $API_SECRET"

# With custom date and authentication
curl -X POST "http://localhost:8888/run-sync?after_date=2025/8/1" \
  -H "Authorization: Bearer $API_SECRET"

# Background sync with date and authentication
curl -X POST "http://localhost:8888/trigger-sync?after_date=2025/7/15" \
  -H "Authorization: Bearer $API_SECRET"
```

## Scheduling

To run the sync automatically, you can use the scheduler script:

```
python scheduler.py
```

Or use the web server which includes automatic scheduling every 3 minutes:

```
python run_server.py
```

You can also set up a cron job to run `python main.py` at regular intervals with specific date parameters.

## Security

The web server uses Bearer token authentication to protect API endpoints:

- **API Secret**: Set `API_SECRET` in your `.env` file
- **Protected Endpoints**: All sync operations require authentication
- **Public Endpoints**: Only status checks (`/`, `/health`) are public
- **Token Format**: Use `Authorization: Bearer YOUR_API_SECRET` header

**Security Best Practices:**
- Use a strong, randomly generated API secret (32+ characters)
- Keep your `.env` file secure and never commit it to version control
- Use HTTPS in production environments
- Regularly rotate your API secret

## Project Structure

- `main.py`: The entry point of the application (supports date parameters)
- `run_server.py`: FastAPI web server with API endpoints for remote control
- `setup.py`: Creates necessary directories for the project
- `scheduler.py`: For automated scheduling of the sync process
- `services/`:
  - `classroom.py`: Handles interaction with the Gmail API to fetch Google Classroom assignments
  - `notion.py`: Manages Notion API operations
  - `assignment_parser.py`: Parses assignment data and formats it for Notion (with system timezone support)
  - `cache_manager.py`: Manages caching of processed assignments to avoid duplicates
  - `google_auth.py`: Handles Google API authentication
- `outputs/`: Contains generated data files and logs
- `cache/`: Stores cache files to track processed assignments

## Features

- **Date filtering**: Specify which assignments to fetch based on date ranges
- **Web API**: Control sync remotely via HTTP endpoints
- **Automatic scheduling**: Built-in 3-minute intervals when using the server
- **Caching**: Avoids duplicate assignments in Notion
- **Timezone support**: Automatically uses system timezone
- **Error handling**: Detailed logging and error reporting

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

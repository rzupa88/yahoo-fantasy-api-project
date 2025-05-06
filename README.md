# Yahoo Fantasy Sports API Project

This project provides a Python interface to access Yahoo Fantasy Sports API data, particularly focused on NFL Fantasy Football data.

## Prerequisites

- Python 3.x
- A Yahoo Developer Account
- Yahoo API credentials (Client ID and Client Secret)

## Setup

1. **Create Yahoo API Credentials**
   - Go to [Yahoo Developer Network](https://developer.yahoo.com/apps/)
   - Create a new application
   - Set the application type as "Installed Application"
   - Set the callback domain as "localhost"
   - Note down your Client ID and Client Secret

2. **Environment Setup**
   Create a `.env` file in the root directory with your Yahoo API credentials:
   ```
   YAHOO_CLIENT_ID=your_client_id_here
   YAHOO_CLIENT_SECRET=your_client_secret_here
   ```

3. **Install Dependencies**
   ```bash
   pip install requests requests_oauthlib python-dotenv
   ```

## Usage

### Authentication

1. Run the script:
   ```bash
   python src/api/yahoo_api.py
   ```

2. The script will:
   - Generate an authorization URL
   - Open your browser for Yahoo login
   - Ask for a verification code
   - Save the access token to `token.json`

### Accessing NFL Player Data

The script provides functionality to:
- Fetch current NFL season data
- Retrieve active NFL players
- Get player rankings and statistics

Example response structure for player data:
```json
{
    "fantasy_content": {
        "game": [{
            "players": {
                "0": {
                    "player": [{
                        "name": "Player Name",
                        "position": "Position",
                        "team": "Team Name",
                        "status": "Status"
                    }]
                }
            }
        }]
    }
}
```

### Available Functions

1. `get_nfl_players(token, count=25)`
   - Fetches NFL player data
   - Parameters:
     - `token`: OAuth token dictionary
     - `count`: Number of players to return (default: 25)
   - Returns: List of player dictionaries

2. `test_api_connection(token)`
   - Tests the API connection
   - Parameters:
     - `token`: OAuth token dictionary
   - Returns: Boolean indicating success/failure

## Error Handling

The script includes error handling for:
- Missing or invalid credentials
- Authentication failures
- API rate limiting
- Invalid responses

## Token Management

- Access tokens are automatically saved to `token.json`
- Tokens include refresh capabilities
- Token expiration is handled automatically

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- SSL certificates (`server.crt` and `server.key`) are used for secure local communication
- Always use HTTPS for API requests

## Troubleshooting

1. **Authentication Errors**
   - Verify your Client ID and Client Secret
   - Ensure your Yahoo Developer Account has proper permissions

2. **API Access Issues**
   - Check your internet connection
   - Verify the token hasn't expired
   - Ensure you're within API rate limits

3. **Data Not Found**
   - Verify the NFL season is active
   - Check if you're requesting valid player positions
   - Ensure the league/game IDs are correct

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
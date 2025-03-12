# ParentPal Backend Infrastructure

This repository contains the backend infrastructure for ParentPal, an AI-powered mobile application designed to support and assist parents. The backend is built with a modular architecture that enables the integration of various AI agents for different parenting-related functionalities.

## Current Features

- **Profile Management System**: Our first implemented AI agent that handles:
  - User and family profiles
  - Profile completion workflows
  - Family relationship management
  - Smart data extraction and validation

## Architecture Overview

The backend is designed with scalability in mind, allowing for the seamless addition of new AI agents and features:
- Modular AI agent system
- Firebase integration for data persistence
- LangChain for AI interactions
- Pydantic for robust data validation
- Asynchronous API design

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ParentPalMVP
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
```

5. Set up Firebase:
- Create a Firebase project
- Generate a service account key
- Place the service account JSON file in `config/firebase/parentpal-service-account.json`

## Running Tests

```bash
python -m tests.agent_tests
```

## Project Structure

- `app/`: Main application code
  - `agents/`: AI agent implementations
    - `main_agent.py`: Central agent router and coordinator
    - `workflow_agent.py`: Base workflow management
    - `profile_agent.py`: Profile management implementation
  - `models/`: Data models and validators
    - `profile_models.py`: Profile-related data structures
  - `services/`: External service integrations
    - `firebase/`: Firebase service implementation
- `tests/`: Test suites
  - `agent_tests.py`: Agent integration tests
  - `deployed_agent_tests.py`: Production environment tests
- `config/`: Configuration files (not tracked in git)
  - `firebase/`: Firebase configuration

## Future Development

The modular architecture allows for easy addition of new features such as:
- Schedule management agent
- Task reminder system
- Parenting advice agent
- Child development tracking
- Educational resource recommendations

## Security Notes

- Never commit sensitive files (`.env`, service account keys, etc.)
- Keep API keys and credentials secure
- Use environment variables for sensitive configuration

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

[Your chosen license]

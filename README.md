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
CLOUD_RUN_API_URL=https://parentpal-backend-1036039487192.us-central1.run.app
```

5. Set up Firebase:
- Create a Firebase project
- Generate a service account key
- For local development:
  ```bash
  # Convert your Firebase service account JSON to base64
  base64 -i path/to/your/service-account.json > firebase_credentials_base64.txt
  
  # Add the base64-encoded credentials to your .env file
  echo "FIREBASE_CREDENTIALS=$(cat firebase_credentials_base64.txt)" >> .env
  ```
- For Cloud Run deployment:
  ```bash
  # Create Artifact Registry repository
  gcloud artifacts repositories create parentpal-repo \
      --repository-format=docker \
      --location=us-central1 \
      --description="ParentPal Docker repository"

  # Configure Docker authentication
  gcloud auth configure-docker us-central1-docker.pkg.dev

  # Build and push the Docker image
  docker build --platform linux/amd64 -t us-central1-docker.pkg.dev/parentpalapp-8f10a/parentpal-repo/parentpal-backend .
  docker push us-central1-docker.pkg.dev/parentpalapp-8f10a/parentpal-repo/parentpal-backend

  # Deploy to Cloud Run
  gcloud run deploy parentpal-backend \
    --image us-central1-docker.pkg.dev/parentpalapp-8f10a/parentpal-repo/parentpal-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --set-env-vars "FIREBASE_CREDENTIALS=$(cat config/firebase/parentpal-service-account.json | base64),OPENAI_API_KEY=your_openai_api_key"
  ```

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
- Base64-encode Firebase credentials for deployment

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

[Your chosen license]

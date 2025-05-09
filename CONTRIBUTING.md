# Contributing to The HigherSelf Network Server

Thank you for your interest in contributing to The HigherSelf Network Server project. This document provides guidelines and instructions for contributing to this codebase.

## Core Principles

All contributions must adhere to the following core principles:

1. **Notion as Central Hub**: Notion serves as the central data and workflow management hub for all operations. Any changes must maintain this architecture.

2. **Pydantic AI Framework**: All data models and Notion interactions must strictly adhere to the Pydantic AI framework and established Notion database structures.

3. **Modularity and Idempotency**: Design for modularity and ensure operations are idempotent to allow for safe retries.

4. **Secure Credential Management**: API tokens and sensitive credentials must be managed securely using environment variables or a designated vault system on The HigherSelf Network Server.

5. **Standardized Logging**: Implement robust error handling and standardized logging for all operations.

## Development Environment Setup

1. Fork the repository on GitHub

2. Clone your fork locally:

   ```bash
   git clone https://github.com/YOUR-USERNAME/The-HigherSelf-Network-Server.git
   cd The-HigherSelf-Network-Server
   ```

3. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # if exists
   ```

5. Set up pre-commit hooks (if configured):

   ```bash
   pre-commit install
   ```

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- Use type hints for all function parameters and return values
- Write docstrings in the Google style format
- Maintain 100% test coverage for new code
- Ensure all Notion database interactions use Pydantic models

## Pull Request Process

1. Create a feature branch from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, ensuring you follow the coding standards

3. Add tests for your changes

4. Update documentation as needed

5. Commit your changes with clear, descriptive messages:

   ```bash
   git commit -m "Add feature X to solve problem Y"
   ```

6. Push to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a pull request against the `main` branch

## Important Guidelines

- **Deployment Target**: All code must be designed to run exclusively on The HigherSelf Network Server
- **Notion Structure**: Do not modify the established Notion database structures
- **Security**: Never commit API tokens or sensitive credentials to the repository
- **Documentation**: Update relevant documentation when adding or modifying features
- **Testing**: All webhook endpoints and Notion interactions must be tested thoroughly

## Getting Help

If you have questions about contributing, please contact The HigherSelf Network's technical team.

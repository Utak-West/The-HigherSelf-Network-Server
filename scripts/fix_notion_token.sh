#!/bin/bash
# Script to fix Notion API token environment issues

# Print current value
echo "Current NOTION_API_TOKEN from environment: $NOTION_API_TOKEN"

# Unset the OS environment variable
unset NOTION_API_TOKEN
echo "Unset NOTION_API_TOKEN environment variable"

# Verify it's gone
echo "After unsetting, NOTION_API_TOKEN is: $NOTION_API_TOKEN"

# Run the inspection script to verify
echo -e "\nRunning environment inspection:"
python inspect_env.py

echo -e "\n----------------------------------------"
echo "Instructions to properly set up your Notion API token:"
echo "1. Edit your .env file and add a valid Notion API token"
echo "   (Must be at least 50 characters long)"
echo "2. Make sure there's no NOTION_API_TOKEN in your OS environment"
echo "   For permanent changes, check your shell startup files:"
echo "   - ~/.bash_profile, ~/.bashrc, ~/.zshrc, etc."
echo -e "----------------------------------------\n"

echo "To add a valid token to your .env file, use:"
echo "echo 'NOTION_API_TOKEN=your_actual_token_here' >> .env"
echo "Or edit .env directly in your text editor."

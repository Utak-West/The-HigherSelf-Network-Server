# Hugging Face Integration Guide

This guide explains how to use the Hugging Face integration in The HigherSelf Network Server.

## Overview

The Hugging Face integration allows you to leverage state-of-the-art NLP models for various tasks directly within your HigherSelf Network workflows. The integration is designed to work seamlessly with Notion as your central data hub.

Key features:
- Access to specialized NLP models for summarization, translation, sentiment analysis, and more
- Process text from Notion pages with Hugging Face models
- Webhook support for triggering Hugging Face processing from external systems
- Task-specific model recommendations

## Configuration

### Environment Variables

Add the following to your `.env` file:

```
# Hugging Face API Key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# AI Router Configuration (Optional)
AI_ROUTER_DEFAULT_PROVIDER=openai  # Change to 'huggingface' if desired
```

You can obtain a Hugging Face API key by:
1. Creating an account at [huggingface.co](https://huggingface.co)
2. Going to your profile settings
3. Generating an API key

## API Endpoints

### Get Hugging Face Integration Info

```
GET /huggingface/
```

Returns information about the Hugging Face integration, including available tasks.

### List Models for a Task

```
GET /huggingface/models/{task}
```

Lists recommended models for a specific task. Available tasks include:
- `text-generation`
- `summarization`
- `translation`
- `sentiment-analysis`
- `question-answering`

### Process Text with Hugging Face

```
POST /huggingface/process
```

Process text from a Notion page using a Hugging Face model and update the page with the result.

Request body:
```json
{
  "notion_page_id": "your-notion-page-id",
  "model_config": {
    "model_id": "facebook/bart-large-cnn",
    "task": "summarization",
    "parameters": {
      "max_length": 100,
      "min_length": 30
    }
  },
  "input_property": "Content",
  "output_property": "Summary",
  "workflow_instance_id": "optional-workflow-id"
}
```

### Notion Webhook

```
POST /huggingface/webhooks/notion
```

Webhook endpoint for Notion automations to trigger Hugging Face processing. Uses the same request format as the `/process` endpoint.

## Using with the AI Router

The Hugging Face provider is integrated with the AI Router, allowing you to use it through the standard AI completion endpoints:

```
POST /ai/completion
```

Request body:
```json
{
  "prompt": "Summarize this text: ...",
  "provider": "huggingface",
  "model": "facebook/bart-large-cnn",
  "max_tokens": 100
}
```

The AI Router will automatically select Hugging Face for certain NLP tasks when detected in the prompt.

## Notion Integration Workflow

A typical workflow for using Hugging Face with Notion:

1. Create a Notion page with text content to process
2. Set up a workflow in Notion that triggers when the page is updated
3. Configure the workflow to call the Hugging Face webhook
4. The server processes the text using the specified Hugging Face model
5. Results are written back to the Notion page
6. Workflow state and history are updated

## Available Models

The integration includes curated lists of recommended models for different tasks:

### Text Generation
- `gpt2` - OpenAI GPT-2 model for text generation
- `distilgpt2` - Distilled version of GPT-2
- `EleutherAI/gpt-neo-1.3B` - GPT-Neo 1.3B parameters model

### Summarization
- `facebook/bart-large-cnn` - BART model fine-tuned on CNN Daily Mail
- `sshleifer/distilbart-cnn-12-6` - Distilled BART for summarization

### Translation
- `Helsinki-NLP/opus-mt-en-fr` - English to French translation
- `Helsinki-NLP/opus-mt-en-es` - English to Spanish translation

### Sentiment Analysis
- `distilbert-base-uncased-finetuned-sst-2-english` - DistilBERT fine-tuned for sentiment

### Question Answering
- `deepset/roberta-base-squad2` - RoBERTa fine-tuned on SQuAD2
- `distilbert-base-cased-distilled-squad` - Distilled BERT for QA

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your Hugging Face API key is correctly set in the `.env` file.

2. **Model Not Found**: Verify that the model ID is correct and publicly available on Hugging Face.

3. **Notion Integration Errors**: Check that the Notion page ID and property names are correct.

### Health Check

You can check the status of the Hugging Face integration using the health endpoint:

```
GET /health
```

The response includes a `huggingface_service` field indicating whether the service is operational.

## Examples

### Summarizing a Document

```python
import requests

response = requests.post(
    "http://your-server/huggingface/process",
    json={
        "notion_page_id": "your-notion-page-id",
        "model_config": {
            "model_id": "facebook/bart-large-cnn",
            "task": "summarization",
            "parameters": {
                "max_length": 150,
                "min_length": 40
            }
        },
        "input_property": "Content",
        "output_property": "Summary",
    },
    headers={"Authorization": "Bearer your-api-key"}
)

print(response.json())
```

### Translating Text

```python
import requests

response = requests.post(
    "http://your-server/huggingface/process",
    json={
        "notion_page_id": "your-notion-page-id",
        "model_config": {
            "model_id": "Helsinki-NLP/opus-mt-en-fr",
            "task": "translation",
            "parameters": {}
        },
        "input_property": "English Text",
        "output_property": "French Translation",
    },
    headers={"Authorization": "Bearer your-api-key"}
)

print(response.json())
```

## Further Resources

- [Hugging Face Documentation](https://huggingface.co/docs)
- [Hugging Face Model Hub](https://huggingface.co/models)
- [Notion API Documentation](https://developers.notion.com/)

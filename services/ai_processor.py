"""Ollama AI integration for processing meeting notes."""

import json
import ollama


# Prompt used to structure raw meeting notes
MEETING_STRUCTURE_PROMPT = """You are a professional meeting notes organizer.

Take the raw meeting notes below and structure them into a clear, professional format.

Extract and organize the following information:

1. MEETING TITLE - Create a concise, descriptive title
2. DATE - Extract the date if available, otherwise use "Not specified"
3. ATTENDEES - List all participants mentioned
4. AGENDA ITEMS - Main topics discussed
5. DISCUSSION POINTS - Key points under each topic
6. DECISIONS MADE - Clear list of decisions
7. ACTION ITEMS - Tasks with assignees and deadlines
8. FOLLOW-UPS - Next steps and follow-up items
9. ADDITIONAL NOTES - Any other important information

Return ONLY valid JSON.

Use exactly this JSON structure:

{
    "title": "Meeting Title",
    "date": "Date if found or Not specified",
    "attendees": [
        "Person 1",
        "Person 2"
    ],
    "agenda_items": [
        "Item 1",
        "Item 2"
    ],
    "discussion_points": [
        {
            "topic": "Topic 1",
            "points": [
                "Point 1",
                "Point 2"
            ]
        }
    ],
    "decisions": [
        "Decision 1",
        "Decision 2"
    ],
    "action_items": [
        {
            "task": "Task description",
            "assignee": "Person",
            "deadline": "Date if specified"
        }
    ],
    "follow_ups": [
        "Follow-up 1",
        "Follow-up 2"
    ],
    "additional_notes": [
        "Note 1",
        "Note 2"
    ]
}

RAW MEETING NOTES:
{text}

Return ONLY the JSON object.
Do not include markdown.
Do not include ```json.
Do not include any explanation."""


async def process_meeting_notes(
    text: str,
    model: str = "qwen2.5:3b"
) -> dict:
    """
    Process raw meeting notes using Ollama AI
    and return structured meeting data.
    """

    try:
        # Make sure the input is a string
        if not isinstance(text, str):
            text = str(text)

        # Remove unnecessary whitespace
        text = text.strip()

        if not text:
            raise ValueError("Meeting notes are empty.")

        # IMPORTANT:
        # Do NOT use .format(text=text) here.
        # The prompt contains JSON braces {}, which would cause
        # Python string formatting errors.
        prompt = MEETING_STRUCTURE_PROMPT.replace("{text}", text)

        # Send request to Ollama
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional meeting notes organizer. "
                        "Always return valid JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json"
        )

        # Get the response content safely
        content = response["message"]["content"]

        if not content:
            raise ValueError("Ollama returned an empty response.")

        # Convert JSON response into Python dictionary
        structured_data = json.loads(content)

        # Make sure the response is a dictionary
        if not isinstance(structured_data, dict):
            raise ValueError("AI response is not a JSON object.")

        # Default structure
        defaults = {
            "title": "Meeting Notes",
            "date": "Not specified",
            "attendees": [],
            "agenda_items": [],
            "discussion_points": [],
            "decisions": [],
            "action_items": [],
            "follow_ups": [],
            "additional_notes": []
        }

        # Add missing fields
        for key, default_value in defaults.items():
            if key not in structured_data:
                structured_data[key] = default_value

        # Make sure list fields have the correct type
        list_fields = [
            "attendees",
            "agenda_items",
            "discussion_points",
            "decisions",
            "action_items",
            "follow_ups",
            "additional_notes"
        ]

        for field in list_fields:
            if not isinstance(structured_data[field], list):
                structured_data[field] = []

        # Make sure title and date are strings
        if not isinstance(structured_data["title"], str):
            structured_data["title"] = "Meeting Notes"

        if not isinstance(structured_data["date"], str):
            structured_data["date"] = "Not specified"

        return structured_data

    except json.JSONDecodeError:
        # Fallback if AI returns invalid JSON
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        return {
            "title": "Meeting Notes",
            "date": "Not specified",
            "attendees": [],
            "agenda_items": [],
            "discussion_points": [
                {
                    "topic": "Discussion",
                    "points": lines
                }
            ],
            "decisions": [],
            "action_items": [],
            "follow_ups": [],
            "additional_notes": [
                "AI returned an invalid JSON response.",
                text
            ],
            "raw_text": text
        }

    except Exception as e:
        raise Exception(f"AI processing failed: {str(e)}")


async def check_ollama_connection() -> bool:
    """
    Check whether Ollama is running and accessible.
    """

    try:
        ollama.list()
        return True

    except Exception:
        return False


async def get_available_models() -> list:
    """
    Get all available Ollama models.
    """

    try:
        models = ollama.list()

        return [
            model["name"]
            for model in models.get("models", [])
        ]

    except Exception:
        return []
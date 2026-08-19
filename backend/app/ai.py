import json

from .config import settings


ALLOWED_CATEGORIES = [
    "IT",
    "HR",
    "Finance",
    "Admin",
    "Other"
]

ALLOWED_PRIORITIES = [
    "Low",
    "Medium",
    "High"
]


def fallback_classification(title, description):

    text = (
        f"{title} {description}"
    ).lower()

    if any(
        word in text
        for word in [
            "vpn",
            "laptop",
            "computer",
            "password",
            "wifi",
            "software"
        ]
    ):
        category = "IT"

    elif any(
        word in text
        for word in [
            "leave",
            "holiday",
            "employee",
            "hr"
        ]
    ):
        category = "HR"

    elif any(
        word in text
        for word in [
            "expense",
            "reimbursement",
            "invoice"
        ]
    ):
        category = "Finance"

    else:
        category = "Other"

    priority = "Medium"

    if any(
        word in text
        for word in [
            "urgent",
            "critical",
            "cannot work",
            "production down"
        ]
    ):
        priority = "High"

    return {
        "category": category,
        "priority": priority
    }


def classify_ticket(title, description):

    if not settings.GROQ_API_KEY:
        return fallback_classification(
            title,
            description
        )

    try:

        from groq import Groq

        client = Groq(
            api_key=settings.GROQ_API_KEY
        )

        prompt = f"""
You classify internal IT helpdesk tickets.

Allowed categories:
IT, HR, Finance, Admin, Other

Allowed priorities:
Low, Medium, High

Return ONLY valid JSON.

Ticket title:
{title}

Ticket description:
{description}

JSON format:
{{
  "category": "IT",
  "priority": "Medium"
}}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        result = json.loads(content)

        category = result.get("category")
        priority = result.get("priority")

        if category not in ALLOWED_CATEGORIES:
            category = "Other"

        if priority not in ALLOWED_PRIORITIES:
            priority = "Medium"

        return {
            "category": category,
            "priority": priority
        }

    except Exception:

        return fallback_classification(
            title,
            description
        )
"""
brief_generator.py
Uses Claude to generate a professional project brief from client intake details.
"""

import anthropic
from config import ANTHROPIC_API_KEY, YOUR_NAME

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are writing a professional project brief for a freelance videographer.
The brief confirms the project scope and sets expectations for both parties.
Write in a clear, professional but friendly tone. Be specific and concise."""


def generate_project_brief(details: dict) -> str:
    """
    Generate a project brief from client intake details.
    Returns the brief as a formatted string.
    """
    company_str = f" at {details['company']}" if details.get('company') else ""
    notes_str = f"\nAdditional notes: {details['notes']}" if details.get('notes') else ""

    prompt = f"""Create a professional project brief for this freelance video project.

Client: {details['client_name']}{company_str}
Project Type: {details['project_type']}
Scope / Deliverables: {details['scope']}
Timeline: {details['timeline']}
Budget: ${details['budget']}{notes_str}

The brief should include:
1. Project Overview (1-2 sentences)
2. Deliverables (bulleted list based on scope)
3. Timeline & Milestones (based on the timeline provided)
4. Investment (the budget amount and payment terms — Net 14 days)
5. Next Steps (contract signing, deposit, kickoff call)

Write it as if {YOUR_NAME} is sending it to the client. Keep it professional but warm.
Use plain text formatting (no markdown — this will be in a PDF)."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()

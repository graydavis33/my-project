"""
intake.py
Collects new client details via CLI prompts.
"""


def collect_client_details():
    """
    Interactive CLI to gather all info needed for onboarding a new client.
    Returns a dict with all client details, or None if cancelled.
    """
    print("\n" + "=" * 55)
    print("  New Client Onboarding")
    print("=" * 55)

    client_name = input("\n  Client name: ").strip()
    client_email = input("  Client email: ").strip()
    company = input("  Company / brand (optional): ").strip()

    print("\n  Project details:")
    project_type = input("  Project type (e.g. Brand Video, Social Content, Event): ").strip()
    scope = input("  Scope / deliverables (e.g. 1 hero video + 5 shorts): ").strip()
    timeline = input("  Timeline (e.g. 3 weeks, deliver by March 30): ").strip()
    budget = input("  Budget / rate ($): ").strip()
    notes = input("  Additional notes (optional): ").strip()

    print(f"\n  Summary:")
    print(f"    Client:   {client_name} <{client_email}>")
    if company:
        print(f"    Company:  {company}")
    print(f"    Project:  {project_type}")
    print(f"    Scope:    {scope}")
    print(f"    Timeline: {timeline}")
    print(f"    Budget:   ${budget}")

    confirm = input("\n  Proceed with onboarding? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return None

    return {
        "client_name": client_name,
        "client_email": client_email,
        "company": company,
        "project_type": project_type,
        "scope": scope,
        "timeline": timeline,
        "budget": budget,
        "notes": notes,
    }

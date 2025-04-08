import re

def extract_description(enriched_report):
    """
    Extracts the Description from the enriched report.
    Looks for a section starting with "**Description:**" and ending at the next header (a line that starts with "**")
    or the end of the text.
    Returns the extracted description or a default message if not found.
    """
    match = re.search(r"\*\*Description:\*\*\s*(.+?)(?=\n\*\*|$)", enriched_report, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "No description provided."

def extract_priority(enriched_report):
    """
    Extracts the Priority from the enriched report.
    Looks for a line like: **Priority:** Medium
    Returns the priority as a string (e.g., "High", "Medium", or "Low").
    """
    match = re.search(r"\*\*Priority:\*\*\s*(\w+)", enriched_report)
    if match:
        return match.group(1).strip()
    return None

def extract_assignee(enriched_report):
    """
    Extracts the Recommended Assignee from the enriched report.
    Looks for a line like: **Recommended Assignee:** Bhavik Patel (Founding Engineer)
    Returns the assignee's name without the role details in parentheses.
    """
    match = re.search(r"\*\*Recommended Assignee:\*\*\s*([^(\n]+)", enriched_report)
    if match:
        # Get the full name and remove any trailing spaces
        name = match.group(1).strip()
        # Remove any text in parentheses and surrounding whitespace
        name = re.sub(r'\s*\([^)]*\)', '', name).strip()
        # Remove any role/title that might come after a dash or comma
        name = re.split(r'[-,]', name)[0].strip()
        return name
    return None

def extract_labels(enriched_report):
    """
    Extracts a list of labels from the enriched report.
    Looks for a line like: **Labels:** Bug, Feature, Improvement
    If no labels are found, it falls back to checking the title for keywords.
    If the title contains 'feature' or 'improvement', returns that label;
    otherwise, it defaults to ['Bug'].
    """
    # Attempt to extract labels from the enriched report.
    match = re.search(r"\*\*Labels:\*\*\s*(.+)", enriched_report)
    if match:
        labels_str = match.group(1)
        extracted_labels = [label.strip() for label in labels_str.split(",") if label.strip()]
        if extracted_labels:
            return extracted_labels

    # Fallback: examine the title for keywords.
    title_match = re.search(r"\*\*Title:\*\*\s*(.+)", enriched_report)
    if title_match:
        title = title_match.group(1).strip().lower()
        if "feature" in title:
            return ["Feature"]
        elif "improvement" in title:
            return ["Improvement"]
    
    # Default label if nothing else is found.
    return ["Bug"]

def extract_title(enriched_report):
    """
    Extracts the Title from the enriched report.
    Looks for a line like: **Title:** Homepage Carousel Not Cycling Through Images
    Returns the title string.
    """
    match = re.search(r"\*\*Title:\*\*\s*(.+)", enriched_report)
    if match:
        return match.group(1).strip()
    return "Bug Report Ticket"

# Quick test of these functions using a sample enriched report.
if __name__ == "__main__":
    sample_report = """
    **Title:** Homepage Carousel Not Cycling Through Images

    **Description:** The homepage carousel is failing to cycle through the images as expected, leading to a static display that impacts user engagement.

    **Priority:** Medium

    **Recommended Assignee:** Bhavik Patel (Founding Engineer)

    **Labels:** bug, ui

    """
    print("Extracted Title:", extract_title(sample_report))
    print("Extracted Priority:", extract_priority(sample_report))
    print("Extracted Assignee:", extract_assignee(sample_report))
    print("Extracted Labels:", extract_labels(sample_report))
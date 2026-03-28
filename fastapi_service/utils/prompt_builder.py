def outline_prompt(title: str, notes: str) -> str:
    return f"""You are a professional book planner and editor.

Create a detailed book outline for a book titled: "{title}"

Editor notes to consider:
{notes}

Your outline should include:
- A brief book description (2-3 sentences)
- 8 to 12 chapter titles, each with a 2-3 sentence description of what that chapter covers

Format your response exactly like this:

Book Description:
[description here]

Chapters:
1. [Chapter Title]
[Chapter description]

2. [Chapter Title]
[Chapter description]

...and so on.

Be specific, structured, and aligned with the editor's notes."""


def outline_regeneration_prompt(title: str, original_outline: str, new_notes: str) -> str:
    return f"""You are a professional book editor refining an existing outline.

Book title: "{title}"

Original outline:
{original_outline}

Editor's revision notes:
{new_notes}

Revise the outline based on the editor's notes. Keep what works, improve what needs changing.
Use the same format as the original outline."""


def chapter_prompt(
    title: str,
    chapter_number: int,
    chapter_title: str,
    chapter_description: str,
    previous_summaries: str,
    chapter_notes: str = None
) -> str:
    notes_section = f"\nEditor notes for this chapter:\n{chapter_notes}" if chapter_notes else ""

    context_section = (
        f"\nContext from previous chapters:\n{previous_summaries}"
        if previous_summaries
        else "\nThis is the first chapter."
    )

    return f"""You are a professional author writing a book titled: "{title}"

{context_section}

Now write Chapter {chapter_number}: {chapter_title}

Chapter description: {chapter_description}
{notes_section}

Guidelines:
- Write in a clear, engaging, and professional tone
- The chapter should be thorough and well-structured
- Use subheadings where appropriate
- Minimum 600 words
- Stay consistent with the tone and content of previous chapters"""


def chapter_regeneration_prompt(
    title: str,
    chapter_number: int,
    chapter_title: str,
    original_content: str,
    revision_notes: str,
    previous_summaries: str
) -> str:
    context_section = (
        f"\nContext from previous chapters:\n{previous_summaries}"
        if previous_summaries
        else ""
    )

    return f"""You are a professional editor revising a chapter of the book titled: "{title}"
{context_section}

Original Chapter {chapter_number}: {chapter_title}
{original_content}

Editor revision notes:
{revision_notes}

Rewrite the chapter addressing the editor's notes. Maintain consistency with previous chapters."""


def summary_prompt(chapter_number: int, chapter_title: str, content: str) -> str:
    return f"""Summarize the following chapter in 150 words or less.
Focus on key events, ideas, and information that would be useful context for writing the next chapter.

Chapter {chapter_number}: {chapter_title}

{content}

Write only the summary, nothing else."""
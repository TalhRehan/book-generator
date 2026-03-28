import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi_service.utils.prompt_builder import outline_prompt, summary_prompt
from fastapi_service.services.openai_service import complete


def test_outline():
    prompt = outline_prompt(
        title="The Art of Deep Work",
        notes="Focus on practical techniques, real-world examples, and productivity science"
    )
    result = complete(prompt)
    assert len(result) > 100
    print("Outline test passed.")
    print(result[:300])


def test_summary():
    sample_content = """
    Chapter 1 explored the concept of deep work and why it matters in a distracted world.
    We looked at how knowledge workers can produce more value by focusing intensely.
    Several case studies from top performers were discussed.
    """
    prompt = summary_prompt(1, "Why Deep Work Matters", sample_content)
    result = complete(prompt, max_tokens=300)
    assert len(result) > 30
    print("\nSummary test passed.")
    print(result)


if __name__ == "__main__":
    test_outline()
    test_summary()
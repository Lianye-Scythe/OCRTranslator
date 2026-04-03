def render_prompt_template(template: str, **variables) -> str:
    rendered = str(template or "")
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{key}}}", str(value or ""))
    return rendered.strip()


def build_image_request_prompt(template: str, *, target_language: str) -> str:
    return render_prompt_template(template, target_language=target_language).strip()


def build_text_request_prompt(template: str, text: str, *, target_language: str) -> str:
    instructions = render_prompt_template(template, target_language=target_language).strip()
    body = (text or "").strip()
    if not body:
        return instructions
    return (
        f"{instructions}\n\n"
        "<text-input>\n"
        f"{body}\n"
        "</text-input>"
    )

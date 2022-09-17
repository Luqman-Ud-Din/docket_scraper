import re


def reset_cookies(request, response):
    request.meta['dont_merge_cookies'] = True
    request.cookies = {}
    return request


def sanitize_text(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def strip_text(text_or_list):
    text_or_list = text_or_list or ''

    if isinstance(text_or_list, str):
        return sanitize_text(text_or_list)

    stripped_texts = []
    for raw_text in text_or_list:
        stripped_text = sanitize_text(raw_text)
        if stripped_text:
            stripped_texts.append(stripped_text)

    return stripped_texts

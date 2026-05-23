"""
Custom exception handler — returns {"error": "message"} to match
the frontend api-client.ts error parsing.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Flatten DRF's nested error dicts into a single "error" string
        errors = response.data

        if isinstance(errors, dict):
            # Collect all messages
            messages = []
            for key, value in errors.items():
                if isinstance(value, list):
                    for item in value:
                        messages.append(str(item))
                else:
                    messages.append(str(value))
            error_message = " ".join(messages)
        elif isinstance(errors, list):
            error_message = " ".join(str(e) for e in errors)
        else:
            error_message = str(errors)

        response.data = {"error": error_message}

    return response

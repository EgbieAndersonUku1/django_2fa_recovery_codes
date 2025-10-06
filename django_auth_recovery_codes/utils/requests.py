import json
from django.http import HttpRequest



def get_request_data(request: HttpRequest) -> dict:
    """
    Return request data as a dictionary, handling JSON and form-encoded POST.
    """
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("JSON body must be a dictionary")
            return data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")
    else:
        # fallback for form-encoded POST or multipart
        return request.POST.dict()

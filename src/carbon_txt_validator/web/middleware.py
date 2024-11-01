class AddTrailingSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.endswith("/"):
            request.path_info = request.path = f"{request.path}/"

        response = self.get_response(request)
        return response

"""User-facing errors. Details stay in server logs."""


class AppError(Exception):
    status_code = 500
    user_message = "The bill could not be generated. Please try again."

    def __init__(self, user_message: str | None = None):
        self.user_message = user_message or self.__class__.user_message
        super().__init__(self.user_message)


class InvalidDateError(AppError):
    status_code = 400


class TemplateError(AppError):
    user_message = "The bill template could not be read. Please try again later."


class RenderError(AppError):
    user_message = "The PDF could not be created. Please try again."


class UnsupportedRuntimeError(AppError):
    user_message = "PDF rendering is not available on this server."

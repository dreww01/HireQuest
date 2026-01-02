# Custom exceptions for the job hunt bot application


class ConfigurationError(Exception):
    pass


class MissingAPIKeyError(ConfigurationError):
    # Raised when a required API key or credential is missing

    def __init__(self, service_name, missing_keys, instructions=None):
        self.service_name = service_name
        self.missing_keys = missing_keys if isinstance(missing_keys, list) else [missing_keys]
        self.instructions = instructions

        keys_str = ', '.join(self.missing_keys)
        message = f"{service_name} configuration incomplete. Missing required credentials: {keys_str}"

        if instructions:
            message += f"\n\n{instructions}"
        else:
            message += f"\n\nPlease set these values in your .env file. See .env.example for reference."

        super().__init__(message)


class InvalidAPIKeyError(ConfigurationError):
    # Raised when API credentials are invalid or authentication fails

    def __init__(self, service_name, details=None):
        self.service_name = service_name
        self.details = details

        message = f"{service_name} authentication failed. The provided credentials are invalid or expired."

        if details:
            message += f"\n\nDetails: {details}"

        message += f"\n\nPlease verify your {service_name} credentials in the .env file."

        super().__init__(message)


class APIConnectionError(Exception):
    # Raised when unable to connect to an external API

    def __init__(self, service_name, original_error=None):
        self.service_name = service_name
        self.original_error = original_error

        message = f"Failed to connect to {service_name} API."

        if original_error:
            message += f"\n\nError: {str(original_error)}"

        super().__init__(message)

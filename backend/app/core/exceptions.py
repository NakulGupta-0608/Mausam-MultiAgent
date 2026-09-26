from typing import Optional


class WeatherServiceException(Exception):
    """Base exception for all weather agent and service failures."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "WEATHER_SERVICE_ERROR",
        detail: Optional[str] = None,
        location: Optional[str] = None,
        retries_attempted: int = 0,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        self.location = location
        self.retries_attempted = retries_attempted


class LocationNotFoundException(WeatherServiceException):
    """Raised when geocoding fails to resolve a valid geographical location."""

    def __init__(
        self,
        location: str,
        detail: Optional[str] = None,
        retries_attempted: int = 0,
    ):
        super().__init__(
            message=f"Location '{location}' could not be resolved. Please verify the spelling or try a major nearby city.",
            status_code=404,
            error_code="LOCATION_NOT_FOUND",
            detail=detail,
            location=location,
            retries_attempted=retries_attempted,
        )


class WeatherApiTimeoutException(WeatherServiceException):
    """Raised when upstream meteorological API requests time out after retries."""

    def __init__(
        self,
        message: str = "Weather API request timed out after multiple retry attempts.",
        location: Optional[str] = None,
        detail: Optional[str] = None,
        retries_attempted: int = 0,
    ):
        super().__init__(
            message=message,
            status_code=504,
            error_code="WEATHER_API_TIMEOUT",
            detail=detail,
            location=location,
            retries_attempted=retries_attempted,
        )


class WeatherApiErrorException(WeatherServiceException):
    """Raised when upstream meteorological API returns a non-200 HTTP response."""

    def __init__(
        self,
        message: str,
        status_code: int = 502,
        detail: Optional[str] = None,
        location: Optional[str] = None,
        retries_attempted: int = 0,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="WEATHER_API_ERROR",
            detail=detail,
            location=location,
            retries_attempted=retries_attempted,
        )


class MalformedResponseException(WeatherServiceException):
    """Raised when upstream API response does not conform to the expected schema."""

    def __init__(
        self,
        message: str = "Weather API returned malformed or unexpected data structure.",
        detail: Optional[str] = None,
        location: Optional[str] = None,
        retries_attempted: int = 0,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="MALFORMED_RESPONSE",
            detail=detail,
            location=location,
            retries_attempted=retries_attempted,
        )

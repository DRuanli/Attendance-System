# app/utils/exceptions.py
class AttendanceSystemException(Exception):
    """Base exception for attendance system."""
    pass

class FaceNotDetectedException(AttendanceSystemException):
    """Raised when no face is detected in image."""
    pass

class MultipleFacesException(AttendanceSystemException):
    """Raised when multiple faces are detected where only one is expected."""
    pass

class EncodingGenerationException(AttendanceSystemException):
    """Raised when face encoding generation fails."""
    pass

class CameraException(AttendanceSystemException):
    """Raised when camera operations fail."""
    pass
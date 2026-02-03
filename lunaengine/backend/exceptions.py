"""
LunaEngine Custom Exceptions

LOCATION: lunaengine/backend/exceptions.py

DESCRIPTION:
This module defines custom exceptions used in the LunaEngine backend.
(For a better understanding of the exceptions)

MODULES PROVIDED:
- exceptions: Custom exceptions for the LunaEngine backend
"""

class LunaEngineException(Exception):
    """Base class for all LunaEngine exceptions"""
    pass

class OpenGLInitializationError(LunaEngineException):
    """Exception raised when OpenGL initialization fails"""
    def __init__(self, message: Exception):
        super().__init__(f'OpenGL Initialization Error: {message}')
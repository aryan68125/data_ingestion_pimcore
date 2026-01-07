from enum import Enum
class ErrorMessages(Enum):
    # default server errors
    INTERNAL_SERVER_ERROR = "Internal server error"
    
    # custom server errors
    FILE_URL_IS_NONE = "File url is required!"
    FILE_TYPE_IS_NONE = "File type is required!"
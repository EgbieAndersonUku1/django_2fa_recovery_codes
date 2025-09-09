from enum import Enum

class CreatedStatus(Enum):
    NOT_CREATED     = "not created"
    CREATED         = "created"
    ALREADY_CREATED = "already created"


class BackendConfigStatus(Enum):
    NOT_CONFIGURED     = "not configured"
    CONFIGURED         = "configured"
    ALREADY_CONFIGURED = "already configured"


class SetupCompleteStatus(Enum):
    NOT_COMPLETE     = "not complete"
    COMPLETE         = "complete"
    ALREADY_COMPLETE = "Already complete"


class ValidityStatus(Enum):
    INVALID = "invalid"
    VALID   = "valid"


class TestSetupStatus(Enum):
    SUCCESS                          = True
    CREATED                          = "The test was successful, recovery codes were successfully created"
    BACKEND_CONFIGURATION_SUCCESS    = "The backend is correctly configured"
    BACKEND_CONFIGURATION_UNSUCCESS  = "Failed to configure the backend"
    SETUP_COMPLETE                   = "The setup was successful"
    SETUP_FAILED                     = "The setup was unsuccessful"
    VALIDATION_COMPLETE              = "The recovery code and recovery batch have correctly setup"
    VALIDATION_UNSUCCESS             = "The recovery code and recovery batch have correctly setup"
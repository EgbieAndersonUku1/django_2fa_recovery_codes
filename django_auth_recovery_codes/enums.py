from enum import Enum

class CreatedStatus(Enum):
    NOT_CREATED     = "The resource has not been created yet."
    CREATED         = "The resource was successfully created."
    ALREADY_CREATED = "The resource has already been created."


class BackendConfigStatus(Enum):
    NOT_CONFIGURED     = "The models associated with the codes have not been configured correctly."
    CONFIGURED         = "The models associated with the codes have been configured successfully."
    ALREADY_CONFIGURED = "The models associated with the codes are already configured."


class SetupCompleteStatus(Enum):
    NOT_COMPLETE     = "The test setup was not completed successfully."
    COMPLETE         = "The test setup has been completed successfully."
    ALREADY_COMPLETE = "The test setup was already completed."


class ValidityStatus(Enum):
    INVALID = "The provided data is invalid."
    VALID   = "The provided data is valid."


class UsageStatus(Enum):
    SUCCESS = "You can now begin using your 2FA recovery codes, please remember to keep them safe"
    FAILURE = "The test failed, check the codes entered and try again or delete your current codes, regenerate new ones, and then try again"


class TestSetupStatus(Enum):
    SUCCESS                          = True
    CREATED                          = "Test successful: recovery codes have been created successfully."
    BACKEND_CONFIGURATION_SUCCESS    = "The backend has been configured successfully."
    BACKEND_CONFIGURATION_UNSUCCESS  = "Failed to configure the backend. Please review the setup."
    SETUP_COMPLETE                   = "The setup process was completed successfully."
    SETUP_FAILED                     = "The setup process failed. Please try again."
    VALIDATION_COMPLETE              = "Validation successful: the recovery code and recovery batch are set up correctly."
    VALIDATION_UNSUCCESS             = "Validation failed: the recovery code and recovery batch could not be set up correctly."

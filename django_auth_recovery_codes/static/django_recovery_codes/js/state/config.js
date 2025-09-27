/**
 * Configuration settings for the application.
 *
 * This file defines flags and constants used throughout the app to control behaviour
 * such as code generation, verification tests, and UI elements. Additional properties
 * may be added as the app grows.
 */


const config = { CODE_IS_BEING_GENERATED: false, 
                 generateCodeActionButtons: false,
                 verificationTestInProgress: false,
                 REGENERATE_CODE_REQUEST: false,
                 LENGTH_PER_DASH: 6,
            };


export default config;
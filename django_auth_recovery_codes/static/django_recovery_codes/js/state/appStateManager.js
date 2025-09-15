import config from "./config.js";

/**
 * appStateManager
 *
 * Manages application state flags in the global config object.
 * Provides methods to update and query different phases of the app lifecycle,
 * such as when code generation or verification tests are in progress or complete.
 * This ensures a centralised, consistent way to toggle and track the app’s state.
 */

export const appStateManager = {
    
    setCodeGeneration(isInProgress) {
        config.CODE_IS_BEING_GENERATED = isInProgress;
    },

    isCodeBeingGenerated() {
        return config.CODE_IS_BEING_GENERATED === true;
    },

    setVerificationTest(isInProgress) {
        config.verificationTestInProgress = isInProgress;
    },

    isVerificationTestInProgress() {
        return config.verificationTestInProgress === true;
    },
    
    shouldGenerateCodeActionButtons() {
        return config.generateCodeActionButtons
    },

    setGenerateActionButtons(generate) {
        config.generateCodeActionButtons = generate;
    },

    setTequestCodeRegeneration(codeRequested) {
        config.REGENERATE_CODE_REQUEST = codeRequested;
      
    },

    setLengthPerDashInputField(length = 6) {
        if (!Number.isInteger(length)) {
            console.error(`The length per dash on the inputfield must be an int. Expected an int got ${length}`);
        }
        config.LENGTH_PER_DASH = length;
    },

    getLengthPerDashInputField() {
        return config.LENGTH_PER_DASH;
    }
};


export default appStateManager;

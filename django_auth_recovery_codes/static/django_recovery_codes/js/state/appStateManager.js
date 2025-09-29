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

    /**
     * Sets whether code generation is currently in progress.
     * 
     * When active, the browser will prompt the user before 
     * closing or refreshing the page (to prevent accidental interruption).
     *
     * @param {boolean} isInProgress - True if code generation is ongoing, false otherwise.
     */
    setCodeGeneration(isInProgress) {
        config.CODE_IS_BEING_GENERATED = isInProgress;
    },

    /**
     * Checks if code generation is currently in progress.
     *
     * @returns {boolean} True if code generation is ongoing, false otherwise.
     */
    isCodeBeingGenerated() {
        return config.CODE_IS_BEING_GENERATED === true;
    },

    /**
     * Sets whether a verification test is currently in progress.
     *
     * @param {boolean} isInProgress - True if verification test is ongoing, false otherwise.
     */
    setVerificationTest(isInProgress) {
        config.verificationTestInProgress = isInProgress;

        if (isInProgress === true) {
            this.setCodeGeneration(true);
            return;
        }
        this.setCodeGeneration(false);
      
    },

    /**
     * Checks if a verification test is currently in progress.
     *
     * @returns {boolean} True if verification test is ongoing, false otherwise.
     */
    isVerificationTestInProgress() {
        return config.verificationTestInProgress === true;
    },

    /**
     * Returns whether action buttons for code generation should be displayed.
     *
     * @returns {boolean} True if code action buttons should be generated, false otherwise.
     */
    shouldGenerateCodeActionButtons() {
        return config.generateCodeActionButtons;
    },

    /**
     * Sets whether action buttons for code generation should be displayed.
     *
     * @param {boolean} generate - True to show buttons, false to hide.
     */
    setGenerateActionButtons(generate) {
        config.generateCodeActionButtons = generate;
    },

    /**
     * Sets whether a request to regenerate code has been made.
     *
     * @param {boolean} codeRequested - True if regeneration is requested, false otherwise.
     */
    setRequestCodeRegeneration(codeRequested) {
        config.REGENERATE_CODE_REQUEST = codeRequested;
    },

    /**
     * Checks whether a request for code regeneration is currently active.
     *
     * @returns {boolean} True if code regeneration has been requested, false otherwise.
     */
    isRequestCodeGenerationActive() {
        return config.REGENERATE_CODE_REQUEST;
    },

    /**
     * Sets the length per dash for the input field.
     *
     * Logs an error if the provided length is not an integer.
     *
     * @param {number} [length=6] - The length per dash. Defaults to 6.
     */
    setLengthPerDashInputField(length = 6) {
        if (!Number.isInteger(length)) {
            console.error(`The length per dash on the input field must be an int. Expected an int got ${length}`);
        }
        config.LENGTH_PER_DASH = length;
    },

    /**
     * Returns the current length per dash for the input field.
     *
     * @returns {number} The configured length per dash.
     */
    getLengthPerDashInputField() {
        return config.LENGTH_PER_DASH;
    }
};


export default appStateManager;

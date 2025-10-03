/**
 * @summary Performs a one-time validation of static DOM elements via `oneTimeElementCheck`.
 *
 * @note This ensures required elements exist before the app starts and avoids repeated
 *       `if (element)` checks. Dynamic elements are excluded since they may not exist
 *       at initial load and must be checked at runtime.
 *
 * === One-Time DOM Element Check ===
 *
 * 1. Purpose
 *    - Ensure all required elements are valid before the app starts.
 *    - Reduce repeated `if (element)` checks in functions.
 *
 * --- Example without `oneTimeElementCheck` ---
 * const form = document.getElementById("form")
 * function someCallingFunction() {
 *     if (form) {
 *         // do something
 *     }
 * }
 *
 * --- Example with `oneTimeElementCheck` ---
 * function someCallingFunction() {
 *     form.appendChild(...)
 * }
 *
 * 2. Dynamic Elements
 *    - Elements not included in `oneTimeElementCheck` are excluded deliberately,
 *      because they are rendered only under certain conditions.
 *
 *    Example:
 *    const emailButtonElement = document.getElementById("email")
 *
 *    This button may be hidden by a Jinja `if` statement and only rendered
 *    when a condition is met (e.g. after generating a code). Until then,
 *    it does not exist in the DOM, so `emailButtonElement` will be `null`.
 *
 * 3. SPA Considerations
 *    - In an SPA, parts of the page update without a full refresh.
 *    - Dynamic elements must therefore be checked when they are used,
 *      not during the initial load.
 *
 * 4. Error Handling
 *    - Attempting to validate dynamic elements in `oneTimeElementCheck`
 *      would cause errors, as they do not exist until after the user action
 *      (and possible refresh) that renders them.
 */

// Default imports
import appStateManager                                         from "../state/appStateManager.js";
import fetchData                                               from "../fetch.js";

// Named imports
import { handleButtonAlertClickHelper }                        from "../helpers/handleButtonAlertClicker.js";
import { handleFormSubmissionHelper }                          from "../helpers/formUtils.js";
import { getCsrfToken }                                        from "../security/csrf.js";
import { clearTestResultContainer, displayResults }            from "./generateSetupElement.js";
import { checkIfHTMLElement, doNothing, toggleElement, 
                      }        from "../utils.js";



const dynamicTestFormSetupElement = document.getElementById("dynamic-form-setup");
const testSetupFormElement        = document.getElementById("verify-setup-form");

const VERIFY_SETUP_BUTTON = "verify-code-btn";
const TEST_SETUP_LOADER   = "verify-setup-code-loader";



const testSetupInputFieldElement = document.getElementById("verify-code-input");

// Same as the above rule
const testVerifySpinnerElement = document.getElementById("verify-setup-code-loader");

export default testSetupInputFieldElement;


let dynamicSetupButton;


/**
 * Performs a one-time validation for static elements to ensure they exist in the DOM.
 * 
 * By validating elements once, we can safely use them in other functions without 
 * repeating `if` checks throughout the code.
 * 
 * Note: This is intended for static elements only. Dynamic elements 
 * (created or fetched at runtime) should be validated when they are used.
 */
function oneTimeElementsCheck() {
    checkIfHTMLElement(dynamicTestFormSetupElement, "Dynamic test form area", true);
}

// call imediately
oneTimeElementsCheck();


if (testSetupFormElement) {
    testSetupFormElement.addEventListener("submit", handleTestSetupFormSubmission);
    testSetupFormElement.addEventListener("input", handleTestSetupFormSubmission);
    testSetupFormElement.addEventListener("blur", handleTestSetupFormSubmission);
}



/**
 * Handles the UI update when a test succeeds or fails.
 *
 * If the test did not fail (`data.FAILURE` is false), this function:
 *   1. Toggles the dynamic test form using `toggleElement`.
 *      - `toggleElement` safely shows or hides a DOM element.
 *   2. Attempts to remove the setup form safely.
 *      - `doNothing` is called if an error occurs (e.g., element does not exist in the DOM).
 *
 * The setup form may not exist initially (e.g., hidden via Jinja),
 * so errors during removal are safely ignored.
 *
 * @param {Object} data - The response data from the test verification.
 */
function handleTestFailure(data) {
    if (data.FAILURE) return;

    toggleElement(dynamicTestFormSetupElement);

    // Attempt to remove the setup form if it exists
    try {
        toggleElement(testSetupFormElement);
    } catch {
        doNothing();
    }
}



/**
 * Verifies the user's test setup when the verification button is clicked.
 *
 * Submits the test setup form, asks the user for confirmation, 
 * sends the verification code to the backend, and shows the results. 
 * It also updates the app state and handles dynamic form elements safely.
 *
 * @param {Event} e - The click event from the verification button.
 * @param {string} verifySetupButtonID - The ID of the button that triggers verification.
 * @returns {Promise<void>} - Resolves when the verification process is finished.
 */
export async function handleTestCodeVerificationSetupClick(e, verifySetupButtonID) {

    const formData = await handleTestSetupFormSubmission(e);
    const MILLI_SECONDS = 10000;

    if (!formData) return;

    const code = formData.verifyCode;

    const alertAttributes = {
        title: "Verify setup",
        text: `⚠️ Important: This application will now verify if your setup was correctly configured with the backend. 
               This is a one-time verification and will not be repeated in the next batch.
               Are you sure you want to continue?`,
        icon: "info",
        cancelMessage: "No worries! No action was taken",
        messageToDisplayOnSuccess: `Great! Your codes are being verified. We’ll let you know once they are ready.
                                    You can continue using the app while we validate them.
                                    Please don't close the page.`,
        confirmButtonText: "Yes, validate setup",
        denyButtonText: "No, don't validate setup"
    };


    /**
    * async Sends the test setup verification code to the backend and returns the response.
    * @returns {Promise<Object>} - The response data from the backend.
    */
    const handleTestSetupFetchAPI = async () => {
        const data = await fetchData({
            url: "/auth/recovery-codes/verify-setup/",
            csrfToken: getCsrfToken(),
            method: "POST",
            body: { code },
            throwOnError: false,
        });

        return data;
    };

    const data = await handleButtonAlertClickHelper(
        e,
        verifySetupButtonID,
        testVerifySpinnerElement,
        alertAttributes,
        handleTestSetupFetchAPI
    );

    if (data) {
        try {
            clearTestResultContainer();
            const isComplete = await displayResults(data);

            handleTestFailure(data);

            testFormSectionElement.reset();

            if (isComplete) {
                appStateManager.setVerificationTest(false);
            }

        } catch (error) {
            doNothing();
            appStateManager.setVerificationTest(false);
        } 

     

    

    }
}



/**
 * Displays the results of a test verification and updates the UI accordingly.
 *
 * This function:
 *   1. Clears any previous test results.
 *   2. Displays the new results using `displayResults`.
 *   3. Toggles dynamic form elements if the test did not fail:
 *      - `toggleElement` shows or hides DOM elements safely.
 *      - `doNothing` prevents errors if an element does not exist (e.g., hidden via Jinja).
 *   4. Resets the test form section.
 *   5. Updates the application state if the test is complete.
 *   6. Ensures the process message is hidden at the end.
 *
 * @param {Object} data - The response data from the test verification.
 */
export async function displayTestResults(data) {
    if (!data) return;

    try {
        clearTestResultContainer();
        const isComplete = await displayResults(data);

        if (!data.FAILURE) {
            toggleElement(dynamicTestFormSetupElement);

            try {
                // Remove the setup form safely
                toggleElement(testSetupFormElement);
            } catch {
                doNothing();
            }
        }

        testFormSectionElement.reset();

        if (isComplete) {
            appStateManager.setVerificationTest(false);
        }
    } catch {
        doNothing();
    } 
}



/**
 * Loads and caches the DOM elements needed for test verification.
 *
 * This function:
 *   1. Hides the process message using `toggleProcessMessage(false)`.
 *   2. Retrieves and caches the dynamic setup button element if not already cached.
 *   3. Retrieves and caches the test verification spinner element if not already cached.
 *
 * @returns {void}
 */
export function loadTestVerificationElements() {

    if (!dynamicSetupButton) {
        dynamicSetupButton = document.getElementById(VERIFY_SETUP_BUTTON);
    }

    if (!testVerifySpinnerElement) {
        testVerifySpinnerElement = document.getElementById(TEST_SETUP_LOADER);
    }
}



/**
 * Handles the submission event for the "delete" form.
 *
 * The function allows the user to submit a request to delete a single recovery
 * codes via a fetch API request when the form is submitted.
 * 
 *
 *
 * @param {Event} e - The submit event triggered by the form.
 * @returns {void}
 */
function handleTestSetupFormSubmission(e) {
    return handleFormSubmissionHelper(e, testSetupFormElement, ["verify_code"]);

}


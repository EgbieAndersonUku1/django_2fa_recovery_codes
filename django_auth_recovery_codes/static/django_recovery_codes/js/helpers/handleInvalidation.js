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



import { handleRecoveryCodeAlert } from "./handleCodeGeneration.js";
import { handleButtonAlertClickHelper } from "./handleButtonAlertClicker.js";
import { handleFormSubmissionHelper } from "./formUtils.js";
import fetchData from "../fetch.js";
import { getCsrfToken } from "../security/csrf.js";
import { checkIfHTMLElement } from "../utils.js";
import { toggleProcessMessage } from "./handleButtonAlertClicker.js";


const invalidateSpinnerElement            = document.getElementById("invalidate-code-loader");
export const invalidateInputFieldElement  = document.getElementById('invalidate-code-input');
const invalidateFormElement               = document.getElementById("invalidate-form");
const INVALIDATE_CODE_BTN_ID              = "invalidate-code-btn";



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
    checkIfHTMLElement(invalidateSpinnerElement,   "Invalidate code spinner", true);
    checkIfHTMLElement(invalidateInputFieldElement,"Invalidate input field",  true);
    checkIfHTMLElement(invalidateFormElement,      "Invalidate form",         true);
}


// Call it immediately
oneTimeElementsCheck();



invalidateFormElement.addEventListener("submit", handleInvalidationFormSubmission);
invalidateFormElement.addEventListener("input", handleInvalidationFormSubmission);
invalidateFormElement.addEventListener("blur", handleInvalidationFormSubmission);



export default invalidateFormElement;

/**
 * Handles the click event for the "Invalidate code" button.
 * 
 * When clicked, this function triggers a Fetch API request to invalidate
 * a single recovery code, provided the required form data is valid.
 * If the form data is invalid, no request is made and no action is taken.
 * 
 * @param {Event} e - The click event triggered by the button.
 * @returns {void}
 */
export async function handleInvalidateButtonClick(e) {
    const formData = await handleInvalidationFormSubmission(e);

    if (!formData) return;

    const code = formData.invalidateCode;

    const alertAttributes = {
        title: "Invalidate Code",
        text: `You are about to invalidate code "${code}". This action cannot be undone. Are you sure you want to proceed?`,
        icon: "warning",
        cancelMessage: "Cancelled – your code is safe.",
        messageToDisplayOnSuccess: `Awesome! Your request to invalidate code "${code}" is being processed.`,
        confirmButtonText: "Yes, invalidate",
        denyButtonText: "No, keep code safe"
    };

    const handleInvalidateCodeFetchAPI = async () => {
        const data = await fetchData({
            url: "/auth/recovery-codes/invalidate-codes/",
            csrfToken: getCsrfToken(),
            method: "POST",
            body: { code: code },
            throwOnError: false,
        });

        return data;
    };

    const data = await handleButtonAlertClickHelper(
        e,
        INVALIDATE_CODE_BTN_ID,
        invalidateSpinnerElement,
        alertAttributes,
        handleInvalidateCodeFetchAPI
    );


    handleRecoveryCodeAlert(data, "Code successfully deactivated", "invalidate");

    invalidateFormElement.reset();
    toggleProcessMessage(false);
}



/**
 * Handles the submission event for the "invalidate" form.
 *
 * The function allows the user to submit a request to invalidate a single recovery
 * codes via a fetch API request when the form is submitted.
 * 
 *
 *
 * @param {Event} e - The submit event triggered by the form.
 * @returns {void}
 */
function handleInvalidationFormSubmission(e) {
    return handleFormSubmissionHelper(e, invalidateFormElement, ["invalidate_code"]);
}

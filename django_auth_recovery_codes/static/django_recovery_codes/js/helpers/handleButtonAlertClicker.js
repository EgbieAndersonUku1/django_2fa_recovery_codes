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


import { toggleSpinner, toggleButtonDisabled, checkIfHTMLElement} from "../utils.js";
import { logError } from "../logger.js";
import { AlertUtils } from "../alerts.js";

const processingMessage = document.getElementById("process-message");


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
    checkIfHTMLElement(processingMessage, "Dynamic test form area", true);
}

oneTimeElementsCheck();

/**
 * Handles a button click event by showing a confirmation alert with spinner and button state toggling.
 * If the alert is confirmed, optionally executes a callback function.
 *
 * @param {Event} e - The click event containing the button element.
 * @param {string} buttonElementID - The ID of the button to listen for; the function proceeds only if the clicked button matches this ID.
 * @param {HTMLElement} buttonSpinnerElement - The spinner element associated with the button, shown while waiting for user response.
 * @param {Object} alertAttributes - Attributes object for the alert dialog.
 * @param {string} alertAttributes.title - The alert title.
 * @param {string} alertAttributes.text - The alert message body.
 * @param {string} alertAttributes.icon - The icon to display in the alert.
 * @param {string} alertAttributes.cancelMessage - Message shown when the alert is cancelled.
 * @param {string} alertAttributes.messageToDisplayOnSuccess - Message to show on successful confirmation.
 * @param {string} alertAttributes.confirmButtonText - Text for the confirm button.
 * @param {string} alertAttributes.denyButtonText - Text for the deny/cancel button.
 * @param {Function} [func=null] - Optional callback function to execute if the alert is confirmed.
 *
 * @returns {Promise<boolean|undefined>} Resolves to the confirmation response (true if confirmed, false if denied).
 *                                      Returns undefined if the clicked button's ID does not match `buttonElementID`.
 */
export async function handleButtonAlertClickHelper(e, buttonElementID, buttonSpinnerElement, alertAttributes = {}, func = null) {

    if (!(typeof alertAttributes === "object")) {
        logError("handleButtonAlertClickHelper", `The parameter alertAttributes is not an object. Expected an object but got type: ${typeof alertAttributes}`);
        return;
    }

    if (!(typeof buttonElementID === "string")) {
        logError("handleButtonAlertClickHelper", `The parameter buttonElementID is not an string. Expected a string but got type: ${typeof buttonElement}`);
        return;
    }

    if (func && !(typeof func === "function")) {
        logError("handleButtonAlertClickHelper", `The parameter func is not a function. Expected a function but got type: ${typeof func}`);
        return;
    }

    const buttonElement = e.target.closest("button");

    if (!buttonElement || buttonElement.tagName !== 'BUTTON' || buttonElement.id !== buttonElementID) {
        return;
    }

    toggleSpinner(buttonSpinnerElement);
    toggleButtonDisabled(buttonElement);

    await new Promise(requestAnimationFrame);

    try {
        let resp = true;

        if (alertAttributes !== null && Object.keys(alertAttributes).length > 0) {

            resp = await AlertUtils.showConfirmationAlert({
                title: alertAttributes.title,
                text: alertAttributes.text,
                icon: alertAttributes.icon,
                cancelMessage: alertAttributes.cancelMessage,
                messageToDisplayOnSuccess: alertAttributes.messageToDisplayOnSuccess,
                confirmButtonText: alertAttributes.confirmButtonText,
                denyButtonText: alertAttributes.denyButtonText
            });

        } 
        if (resp) {
            
            toggleProcessMessage(true);

            if (func) {
                return func()
            }
        }

        return resp;

    } finally {
        toggleSpinner(buttonSpinnerElement, false);
        toggleButtonDisabled(buttonElement, false);
      
    }


}


/**
 * Toggles the visibility of the processing message element.
 *
 * @param {boolean} [show=true] - Whether to show (true) or hide (false) the message.
 */
export function toggleProcessMessage(show=true) {
    show ? processingMessage.classList.add("show") : processingMessage.classList.remove("show")
}
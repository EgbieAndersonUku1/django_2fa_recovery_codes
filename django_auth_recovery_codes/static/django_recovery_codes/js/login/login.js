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

import { handleInputFieldHelper } from "../helpers/handlers.js";
import { showSpinnerFor, checkIfHTMLElement } from "../utils.js";


const loginForm       = document.getElementById("login-recovery-form");
const loginInputField = document.getElementById("recovery-code-input");
const spinner         = document.getElementById("login-recovery-loader");



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
    checkIfHTMLElement(loginForm,       "Login form",         true);
    checkIfHTMLElement(loginInputField, "Login input field",  true);
    checkIfHTMLElement(spinner,         "Login spinner",      true);
}


// Call it immediately
oneTimeElementsCheck();


loginInputField.addEventListener("input", handleInputFieldHelper);
loginForm.addEventListener("submit", handleLoginFormSubmission);



/**
 * Handles the login form submission with a temporary spinner display.
 *
 * - Prevents the default form submission.
 * - Shows a spinner for a short duration before submitting the form.
 *
 * @param {Event} e - The submit event from the login form.
 */
function handleLoginFormSubmission(e) {
    e.preventDefault();
    const MILLI_SECONDS = 2000;

    showSpinnerFor(spinner, MILLI_SECONDS);

    setTimeout(() => {
        loginForm.submit();
    }, MILLI_SECONDS);

    
}




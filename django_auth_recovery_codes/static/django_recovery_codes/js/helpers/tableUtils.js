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


import appStateManager from "../state/appStateManager.js";
import { generateCodeActionAButtons } from "../generateCodeActionButtons.js";
import { toggleSpinner, clearElement, checkIfHTMLElement } from "../utils.js";

const PAGE_ELEMENT_ID                     = "page-buttons";
let   codeActionContainerElement          = document.getElementById(PAGE_ELEMENT_ID);
const tableCoderSpinnerElement            = document.getElementById("table-loader");
const codeTableElement                    = document.getElementById("table-code-view");
const generaterecoveryBatchSectionElement = document.getElementById("generate-code-section");
const messageContainerElement             = document.getElementById("messages");
const messagePTag                         = document.getElementById("message-p-tag");

import { HTMLTableBuilder } from "../generateTable.js";




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
    checkIfHTMLElement(codeActionContainerElement,          "Code action container", true);
    checkIfHTMLElement(tableCoderSpinnerElement,            "Table loader spinner",  true);
    checkIfHTMLElement(codeTableElement,                    "Code table view",       true);
    checkIfHTMLElement(messageContainerElement,             "Message container",     true);
    checkIfHTMLElement(messagePTag,                         "Message <p> tag",       true);

   
}
oneTimeElementsCheck();



/**
 * Populates the UI table with user recovery codes and manages the associated spinner and messages.
 *
 * @param {Array<Object>} codes - Array of recovery code objects to populate the table.
 * @returns {boolean} Always returns true to indicate the operation was attempted.
 */
export function populateTableWithUserCodes(codes) {

    const tableObjectData = {
        classList: ["margin-top-lg"],
        id: "generated-codes-table",

    }

    const MILLI_SECONDS = 6000; // seconds is only for the message. It takes 5 seconds to make it journey up and down
    const colHeaders    = ["status", "codes"];

    const tableElement = HTMLTableBuilder(colHeaders, codes, tableObjectData);

    if (tableElement) {

        messageContainerElement.classList.add("show");
        messagePTag.textContent = "Your recovery codes are now ready...";

        setTimeout(() => {

            tableCoderSpinnerElement.style.display = "none"

            toggleSpinner(tableCoderSpinnerElement, false);
            addCodeToTableAndButtons(tableElement)
            messageContainerElement.classList.remove("show");

            appStateManager.setCodeGeneration(false)

            if (generaterecoveryBatchSectionElement === null) {
                clearElement(codeActionContainerElement);

            }

        }, MILLI_SECONDS)

    }

    return true;
}



/**
 *  Add the codes to the table along with the buttons. Clears everything 
 *  first to prevent duplication
 * 
 * @param {HTMLElement} tableCodesElement - The table element containing user recovery codes.
 */
function addCodeToTableAndButtons(tableCodesElement) {

    if (appStateManager.shouldGenerateCodeActionButtons()) {
       showCodeActionsButton();
    }

    if (codeTableElement) {
        clearElement(codeTableElement);
        codeTableElement.appendChild(tableCodesElement);
        return;
    }

    clearElement(tableCodeContainerDiv);
    tableCodeContainerDiv.appendChild(tableCodesElement);


}


/**
 * Returns the DOM element that contains the code action buttons.
 *
 * @returns {HTMLElement|null} The code action buttons container element, or null if not found.
 */
function fetchCodeActionButtonsArea() {
    return document.getElementById("code-actions");
}



/**
 * Displays the code action buttons in the designated container.
 *
 * - Fetches the container if it hasn't been cached yet.
 * - Clears any existing content in the container.
 * - Generates and appends the action buttons.
 * - Updates the app state to indicate code generation is complete.
 */
function showCodeActionsButton() {
    if (!codeActionContainerElement) {
        codeActionContainerElement = fetchCodeActionButtonsArea();
    }

    
    clearElement(codeActionContainerElement);
    const buttons = generateCodeActionAButtons();
    codeActionContainerElement.appendChild(buttons);
    appStateManager.setCodeGeneration(false);
    return;
}
  
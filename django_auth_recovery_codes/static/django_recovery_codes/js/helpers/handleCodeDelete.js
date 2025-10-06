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


import { handleRecoveryCodeAlert }      from "./handleCodeGeneration.js";
import { handleFormSubmissionHelper }   from "./formUtils.js";
import { handleButtonAlertClickHelper } from "./handleButtonAlertClicker.js";
import fetchData                        from "../fetch.js";
import { getCsrfToken }                 from "../security/csrf.js";
import { checkIfHTMLElement, 
         getOrFetchElement, 
         toggleElement }                from "../utils.js";
import { AlertUtils }                   from "../alerts.js";
import { markCardAsDeleted }            from "../batchCardsHistory/markCardAsDeleted.js";
import { getCurrentCard }               from "../batchCardsHistory/updateBatchHistorySection.js";
import { clearElement, safeUIUpdate }   from "../utils.js";


const PAGE_ACTION_BUTTONS_ID              = "page-buttons";
const TABLE_ID                            = "table-code-view";
export const deleteInputFieldElement      = document.getElementById("delete-code-input");

const DELETE_ALL_LOADER_ID                = "delete-all-code-loader"
const testSetupFormContainerElement       = document.getElementById("dynamic-verify-form-container");
const deleteAllCodeButtonSpinnerElement   = document.getElementById(DELETE_ALL_LOADER_ID); // Dynamic, doesn't exist at runtime
const deleteCodeButtonSpinnerElement      = document.getElementById("delete-current-code-loader");
const deleteFormElement                   = document.getElementById("delete-form");
let   pageCodeActionButtonsElements       = document.getElementById(PAGE_ACTION_BUTTONS_ID);
const tableCodeElements                   = document.getElementById(TABLE_ID);



/**
 * Performs a one-time validation for static elements to ensure they exist in the DOM.
 * 
 * By validating elements once, we can safely use them in other functions without 
 * repeating `if` checks throughout the code.
 * 
 * Note: This is intended for static elements only. Dynamic elements 
 * (created or fetched at runtime) should be validated when they are used.
 * One-time validation for delete-related static elements.
 */
export function oneTimeElementsCheck() {
    checkIfHTMLElement(deleteInputFieldElement,        "Delete input field",        true);
    checkIfHTMLElement(testSetupFormContainerElement,  "Test setup form container", true);
    checkIfHTMLElement(deleteFormElement,              "Delete form",               true);
    checkIfHTMLElement(pageCodeActionButtonsElements,  "Buttons containings action buttons set", true);
    checkIfHTMLElement(tableCodeElements,              "Table containing codes",     true);
}

// call immediately
oneTimeElementsCheck();


deleteFormElement.addEventListener("submit", handleDeleteFormSubmission);
deleteFormElement.addEventListener("input", handleDeleteFormSubmission);
deleteFormElement.addEventListener("blur", handleDeleteFormSubmission);

export default deleteFormElement;




/**
 * Toggles off (hides) multiple UI elements related to code actions.
 *
 * @param {...HTMLElement} elements - One or more DOM elements to toggle.
 */
function toggleCodeUIElementsOff(...elements) {
    elements.forEach(el => {
        if (el) toggleElement(el, false); 
    });
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
export function handleDeleteFormSubmission(e) {
    return handleFormSubmissionHelper(e, deleteFormElement, ["delete_code"]);

}



/**
 * Returns the dynamic UI elements related to code actions.
 *
 * @returns {Object} An object containing references to the code action buttons and table elements.
 * @property {HTMLElement|null} codeActionButtons - The element for code action buttons, or null if not found.
 * @property {HTMLElement|null} tableCodes - The element for the code table, or null if not found.
 */
function getDynamicCodeUIElements() {
    return {
        codeActionButtons: document.getElementById("code-actions"),
        tableCodes: document.getElementById("table-code-view")
    };
}


function showSuccessDeleteAlert() {
    AlertUtils.showAlert({
        title: "Codes Deleted",
        text: "All your codes have been deleted. Refresh the page to generate new ones.",
        icon: "success",
        confirmButtonText: "OK"
    })
}


/**
 * Toggles visibility of multiple elements.
 *
 * @param  {...HTMLElement} elements - The elements to toggle.
 */
function toggleAlertAndFormElements(alertMessage) {

    const SUCCESS_ALERT_SELECTOR = ".alert-message";
    const dynamicAlertElement    = document.querySelector(SUCCESS_ALERT_SELECTOR);

    toggleElement(dynamicAlertElement);
    toggleElement(alertMessage);
    toggleElement(testSetupFormContainerElement);
}





/**
 * Handles the click event for the "Invalidate code" button.
 * 
 * When clicked triggers a fetch API that allows the user to 
 * delete a single recovery code
 * 
 * @param {Event} e - The click event triggered by the button.
 */
export async function handleDeleteCodeeButtonClick(e, deleteButtonID) {

    const formData = await handleDeleteFormSubmission(e);

    if (!formData) return;

    const code = formData.deleteCode;

    if (formData) {
        const alertAttributes = {
            title: "Delete code",
            text: `Doing this will delete the code "${code}". This action cannot be reversed. Are you sure you want to go ahead?`,
            icon: "warning",
            cancelMessage: "No worries! Your code is safe.",
            messageToDisplayOnSuccess: "Awesome! Your code is being processed, please wait...",
            confirmButtonText: "Yes, delete code",
            denyButtonText: "No, don't delete code"
        }

        const handleRemoveRecoveryCodeApiRequest = async () => {

            const data = await fetchData({
                url: "/auth/recovery-codes/delete-codes/",
                csrfToken: getCsrfToken(),
                method: "POST",
                body: { code: code },
                throwOnError: false,
            });

            return data
        };

        const data = await handleButtonAlertClickHelper(e,
            deleteButtonID,
            deleteCodeButtonSpinnerElement,
            alertAttributes,
            handleRemoveRecoveryCodeApiRequest
        );

        const MILLI_SECONDS = 1000;

         safeUIUpdate(() => {
                handleRecoveryCodeAlert(data, "Code successfully deleted", "delete");
        }, MILLI_SECONDS);
        
        deleteFormElement.reset()

    };


}



function handleBadRequestFromServer() {
    pageCodeActionButtonsElements = getOrFetchElement(pageCodeActionButtonsElements, PAGE_ACTION_BUTTONS_ID)
    clearElement(pageCodeActionButtonsElements);
      
}


/**
 * Handles the click event for the "delete all code" button.
 * 
 * When clicked triggers a fetch API that allows the user to 
 * email themselves their recovery code.
 * 
 * Note: The process can only be done once meaning 
 * @param {Event} e - The click event triggered by the button.
 */
export async function handleDeleteAllCodeButtonClick(e,  deleteAllCodesButtonID) {

    const alertAttributes = {
        title: "Delete All codes?",
        text: "This action will delete all your existing recovery codes. Would you like to proceed?",
        icon: "warning",
        cancelMessage: "No worries! Your codes are safe.",
        messageToDisplayOnSuccess: "All your recovery codes have been deleted.",
        confirmButtonText: "Yes, delete existing codes",
        denyButtonText: "No, take me back"
    }

    // function
    const handleDeleteAllCodesApiRequest = async () => {
        let resp;
        try {
             resp = await fetchData({url: "/auth/recovery-codes/mark-batch-as-deleted/",
                                            csrfToken: getCsrfToken(),
                                            method: "POST",
                                            body: {forceUpdate: true},
                                     });
            return resp;
        } catch (error) {
            resp = {}
            resp.SUCCESS = false;
            return resp;
        }
      

        

    }

    const resp = await handleButtonAlertClickHelper(e,
                        deleteAllCodesButtonID,
                        getOrFetchElement(deleteAllCodeButtonSpinnerElement, DELETE_ALL_LOADER_ID),
                        alertAttributes,
                        handleDeleteAllCodesApiRequest,
                    )
   
    if (!resp) {
        handleBadRequestFromServer();
        return;
    }

    if (resp.SUCCESS) {

        const {codeActionButtons, tableCodes} = getDynamicCodeUIElements();
       
        if (!(checkIfHTMLElement(codeActionButtons) && checkIfHTMLElement(tableCodes))) {
            warnError("handleDeleteAllCodeButtonClick", "The button container element wasn't found");
            return;
        }
        clearElement(codeActionButtons);
        markCardAsDeleted(getCurrentCard());
        toggleCodeUIElementsOff(codeActionButtons, tableCodes);
        showSuccessDeleteAlert();
        toggleAlertAndFormElements();
        deleteCodeRelatedElements();

        try {
            toggleElement(testSetupFormElement)
        } catch (error) {
            
             deleteCodeRelatedElements();
            }

        }  

} 


function deleteCodeRelatedElements() {
    
    handleBadRequestFromServer();
    clearElement(getOrFetchElement(tableCodeElements, TABLE_ID));
}
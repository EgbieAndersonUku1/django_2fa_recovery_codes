import {
    checkIfHTMLElement,
    showSpinnerFor,
    toggleSpinner,
    applyDashToInput,
    sanitizeText,
    toggleButtonDisabled,
    getCsrfToken
} from "./utils.js";

import { parseFormData } from "./form.js";
import { AlertUtils } from "./alerts.js";
import { logError, warnError } from "./logger.js";
import fetchData from "./fetch.js";
import { HTMLTableBuilder } from "./generateTable.js";


// Elements
const recovryDashboardElement = document.getElementById("recovery-dashboard");
const daysToExpiryGroupWrapperElement = document.getElementById("days-to-expiry-group");
const navigationIconContainerElement = document.getElementById("navigation-icon-elements");
const generateCodeSectionElement = document.getElementById("generate-code-section");
const codeTableElement = document.getElementById("table-code-view");

// spinner elements
const generateCodeWithExirySpinnerElement = document.getElementById("generate-code-loader");
const generateCodeWithNoExpirySpinnerElement = document.getElementById("generate-code-without-expiry-loader");
const excludeSpinnerLoaderElement = document.getElementById("exclude-expiry-loader");
const regenerateButtonSpinnerElement = document.getElementById("re-generate-code-loader")
const emailButtonSpinnerElement = document.getElementById("email-code-loader");
const deleteCodeButtonSpinnerElement = document.getElementById("delete-current-code-loader");
const deleteAllCodeButtonSpinnerElement = document.getElementById("delete-all-code-loader");
const downloadCodeButtonElementSpinner = document.getElementById("download-code-loader");
const invalidateSpinnerElement = document.getElementById("invalidate-code-loader");
const tableCoderSpinnerElement = document.getElementById("table-loader");

// button elements
const generateButtonElement = document.getElementById("generate-code-button-wrapper");



// forms elements

// generate code with expiry form element
const generateCodeWithExpiryFormElement = document.getElementById("generate-form-code-with-expiry");


// invalidate code form elements
const invalidateFormElement = document.getElementById("invalidate-form");
const invalidateInputFieldElement = document.getElementById('invalidate-code-input');


// delete code form
const deleteFormElement = document.getElementById("delete-form");
const deleteInputFieldElement = document.getElementById("delete-code-input")


// event handlers
recovryDashboardElement.addEventListener("click", handleEventDelegation);


// form elements event handlers
generateCodeWithExpiryFormElement.addEventListener("submit", handleGenerateCodeWithExpiryFormSubmission);
invalidateInputFieldElement.addEventListener("input", handleInputFieldHelper);
deleteInputFieldElement.addEventListener("input", handleInputFieldHelper);
invalidateFormElement.addEventListener("click", handleInvalidateButtonClick)


// invalidate code form elements
invalidateFormElement.addEventListener("submit", handleInvalidationFormSubmission);
invalidateFormElement.addEventListener("input", handleInvalidationFormSubmission);
invalidateFormElement.addEventListener("blur", handleInvalidationFormSubmission);

// delete code form elements 
deleteFormElement.addEventListener("submit", handleDeleteFormSubmission);
deleteFormElement.addEventListener("input", handleDeleteFormSubmission);
deleteFormElement.addEventListener("blur", handleDeleteFormSubmission);


// messages elements
const messageContainerElement = document.getElementById("messages");
const messagePTag = document.getElementById("message-p-tag");


// navigation icon
const hamburgerOpenIcon = document.getElementById("open-hamburger-nav-icon");
const closeXIcon = document.getElementById("close-nav-icon");


// Stats display board
const statsTotalCodesIssuedBoard = document.getElementById("stat__total_codes_issued")
const statsTotalCodesDownloadedBoard = document.getElementById("stat__total-codes-downloaded");
const statsTotalCodesEmailedBoard = document.getElementById("stat__total-codes-emailed");
const statsBatchCodesRemovedBoard = document.getElementById("stat__total-batch-codes-removed");
const statsCodesDeactivatedBoard = document.getElementById("stat__total-codes-deactivated");
const statsTotalCodesRemovedBoard = document.getElementById("stat__total-codes-removed")


// constants
const MILLI_SECONDS_BEFORE_DISPLAY = 1000;
const REGENERATE_BUTTON_ID = "regenerate-code-btn";
const EMAIL_BUTTON_ID = "email-code-btn";
const DELETE_CURRENT_CODE_BUTTON_ID = "delete-current-code-btn";
const DELETE_ALL_CODES_BUTTON_ID = "delete-all-code-btn"
const DOWNLOAD_CODE_BTN_ID = "download-code-btn";
const INVALIDATE_CODE_BTN = "invalidate-code-btn";
const GENERATE_CODE_WITH_EXPIRY_BUTTON = "form-generate-code-btn";
const GENERATE_CODE_WITH_NO_EXPIRY = "generate-code-with-no-expiry-btn";
const OPEN_NAV_BAR_HAMBURGERR_ICON = "open-hamburger-nav-icon";
const CLOSE_NAV_BAR_ICON = "close-nav-icon";


// configuration
const config = { CODE_IS_BEING_GENERATED: false };


window.addEventListener("resize", handleResetDashboardState);


function codeIsBeingGenerated() {
    config.CODE_IS_BEING_GENERATED = true;
}


function codeGenerationComplete() {
    config.CODE_IS_BEING_GENERATED = false;
}



window.addEventListener("beforeunload", function (event) {
  if (config.CODE_IS_BEING_GENERATED) {
        event.preventDefault();
        event.returnValue = ""; 
        return "";
    }
});



function handleEventDelegation(e) {
    const buttonElement = e.target.closest("button");
    const inputElement = e.target.closest("input");
    const navigationIconElement = e.target.closest("i");


    if (buttonElement === null && inputElement === null && navigationIconElement === null) {
        return;
    }


    // Decide which element's ID to use:
    // Prefer buttonElement's id if it exists, otherwise use inputElement's id if exists, if not use the navigation elements id
    const elementID = buttonElement ? buttonElement.id : (inputElement ? inputElement.id : navigationIconElement.id);
 

    switch (elementID) {
        case GENERATE_CODE_WITH_EXPIRY_BUTTON:
            codeIsBeingGenerated();
            handleGenerateCodeWithExpiryClick(e);
            break;
        case GENERATE_CODE_WITH_NO_EXPIRY:
            codeIsBeingGenerated();
            handleGenerateCodeWithNoExpiryClick(e);
            break;
        case EMAIL_BUTTON_ID:
            handleEmailCodeeButtonClick(e);
            break;
        case "exclude_expiry":
            handleIncludeExpiryDateCheckMark(e);
            break;
        case REGENERATE_BUTTON_ID:
            handleRegenerateCodeButtonClick(e);
        case DELETE_CURRENT_CODE_BUTTON_ID:
            handleDeleteCodeeButtonClick(e);
            break;
        case DELETE_ALL_CODES_BUTTON_ID:
            handlDeleteAllCodeButtonClick(e);
            break;
        case DOWNLOAD_CODE_BTN_ID:
            handleDownloadButtonClick(e);
            break;
        case OPEN_NAV_BAR_HAMBURGERR_ICON:
            toggleSideBarIcon(navigationIconElement)
            break;

        case CLOSE_NAV_BAR_ICON:
            toggleSideBarIcon(navigationIconElement);
            break;

    }

}


/**
 * 
 * --------------------------------------------------------------------
 * Handlers
 * --------------------------------------------------------------------
 * 
 *  
 * 
 * */

/**
 * Resets certain dashboard elements to their default state on large screens (≥ 990px).
 */
function handleResetDashboardState() {
    const EXPECTED_WINDOW_WIDTH = 990;
    const currentWindowSize = window.innerWidth;

    hamburgerOpenIcon.style.display = "block";
    closeXIcon.style.display = "none";

    // Desktop view or greater
    if (currentWindowSize > EXPECTED_WINDOW_WIDTH) {
        recovryDashboardElement.style.paddingTop = "65px";
        recovryDashboardElement.style.marginTop = "0";
        navigationIconContainerElement.style.height = 0
        hamburgerOpenIcon.style.display = "none"

    }

}



/**
 * Handles the click event for the "Generate Code" button.
 * 
 * Intended to generate recovery codes on the backend via the Fetch API.
 * 
 * @param {Event} e - The click event triggered by the button.
 */
async function handleGenerateCodeWithExpiryClick(e) {

    const formData = await handleGenerateCodeWithExpiryFormSubmission(e);

    if (formData) {
        const daysToExpiry = parseInt(formData.daysToExpiry);

        const alertAttributes = {
            title: "Generate Code",
            text: `
                ⚠️ Important: This will generate 10 new recovery codes and remove any unused ones.
                They will be valid for only ${daysToExpiry} ${daysToExpiry === 1 ? 'day' : 'days'}.
                Are you sure you want to continue?
                    `,
            icon: "info",
            cancelMessage: "No worries! No action was taken",
            messageToDisplayOnSuccess: `
                Great! Your codes are being generated in the background and will be displayed in View Generated Codes section once ready.
                You can continue using the app while we prepare them.
                We’ll notify you once they’re ready.
                Please, don't close the page.
            `,
            confirmButtonText: "Yes, generate codes",
            denyButtonText: "No, don't generate codes"
        };


        handleRecoveryCodesAction({
            e:e,
            generateCodeBtn: GENERATE_CODE_WITH_EXPIRY_BUTTON,
            generateCodeBtnSpinnerElement: generateCodeWithExirySpinnerElement,
            alertAttributes: alertAttributes,
            url: "/auth/recovery-codes/generate-with-expiry/",
            daysToExpiry: daysToExpiry,

        })

    }

}



/**
 * Handles the click event for the "Generate Code" button.
 * 
 * Intended to generate recovery codes on the backend via the Fetch API.
 * 
 * @param {Event} e - The click event triggered by the button.
 */
async function handleGenerateCodeWithNoExpiryClick(e) {

    const alertAttributes = {
        title: "Generate Code",
        text: `⚠️ Important: This will generate 10 new recovery codes. 
                    They will be valid for an indefinite period unless deleted or invalidated. 
                    Are you sure you want to continue?`,
        icon: "info",
        cancelMessage: "No worries! No action was taken",
        messageToDisplayOnSuccess: `
                Great! Your codes are being generated in the background and will be displayed in View Generated Codes section once ready.
                You can continue using the app while we prepare them.
                We’ll notify you once they’re ready.
                Please, don't close the page.
            `,
        confirmButtonText: "Yes, generate codes",
        denyButtonText: "No, don't generate codes"
    };

    handleRecoveryCodesAction({
            e:e,
            generateCodeBtn: GENERATE_CODE_WITH_NO_EXPIRY,
            generateCodeBtnSpinnerElement: generateCodeWithNoExpirySpinnerElement,
            alertAttributes: alertAttributes,
            url: "/auth/recovery-codes/generate-without-expiry/",
           
        })
   
}



/**
 * Handles the click event for the "Download code" button.
 * 
 * When clicked triggers a fetch API that allows the user to download
 * the recovery codes
 * 
 * @param {Event} e - The click event triggered by the button.
 */
async function handleDownloadButtonClick(e) {

    const MILLI_SECONDS = 5000;
    const buttonElement = e.target

    showSpinnerFor(downloadCodeButtonElementSpinner, MILLI_SECONDS);
    messageContainerElement.classList.add("show");

    toggleButtonDisabled(buttonElement)

    messagePTag.textContent = "Preparing your download... just a moment!";

    setTimeout(() => {

        toggleButtonDisabled(buttonElement, false)
        messageContainerElement.classList.remove("show");

        // fetch ap1

        // simulate fetch api
        const respData = {
            TOTAL_ISSUED: 0,
            TOTAL_USED: 0,
            TOTAL_DEACTIVATED: 0,
            TOTAL_REMOVED: 0,
            TOTAL_DOWNLOADED: 1,
            TOTAL_EMAILED: 0,
            BATCH_REMOVED: 0,
            SUCCESS: true,
        }

        statsTotalCodesDownloadedBoard.textContent = respData.TOTAL_DOWNLOADED;

    }, MILLI_SECONDS)


}



/**
 * Handles the click event for the "Invalidate code" button.
 * 
 * When clicked, this function triggers a Fetch API request to invalidate
 * a single recovery code, provided the required form data is valid when submitted.
 * If the form data is invalid, no request is made and no action is taken.
 * 
 * @param {Event} e - The click event triggered by the button.
 * @returns {void}
 */
async function handleInvalidateButtonClick(e) {
    const formData = await handleInvalidationFormSubmission(e);

    if (formData) {
        const alertAttributes = {
            title: "Invalidate code",
            text: "Doing this will invalidate this code. This action cannot be undone. Are you sure you want to go ahead?",
            icon: "warning",
            cancelMessage: "No worries! Your code is safe.",
            messageToDisplayOnSuccess: "Awesome! Your code has been invalidated.",
            confirmButtonText: "Yes, invalidate",
            denyButtonText: "No, don't invalidate code"
        }

        const handleInvalidateCodeFetchAPI = () => {
            const respData = {
                TOTAL_ISSUED: 0,
                TOTAL_USED: 0,
                TOTAL_DEACTIVATED: 1,
                TOTAL_REMOVED: 0,
                TOTAL_DOWNLOADED: 0,
                TOTAL_EMAILED: 0,
                BATCH_REMOVED: 0,
                SUCCESS: true,
            }
            invalidateFormElement.reset();
            return respData;
        }

        const resp = await handleButtonAlertClickHelper(e, INVALIDATE_CODE_BTN, invalidateSpinnerElement, alertAttributes, handleInvalidateCodeFetchAPI);
        if (resp.SUCCESS) {
            statsCodesDeactivatedBoard.textContent = resp.TOTAL_DEACTIVATED
        }

    }

}



/**
 * Handles the click event for the "Invalidate code" button.
 * 
 * When clicked triggers a fetch API that allows the user to 
 * delete a single recovery code
 * 
 * @param {Event} e - The click event triggered by the button.
 */
async function handleDeleteCodeeButtonClick(e) {

    const formData = await handleDeleteFormSubmission(e);

    if (formData) {
        const alertAttributes = {
            title: "Delete code",
            text: "Doing this will delete this current code. This action cannot be reversed. Are you sure you want to go ahead?",
            icon: "warning",
            cancelMessage: "No worries! Your code is safe.",
            messageToDisplayOnSuccess: "Awesome! Your code has been deleted.",
            confirmButtonText: "Yes, delete code",
            denyButtonText: "No, don't delete code"
        }

        const handleRemoveRecoveryCodeApiRequest = () => {
            const respData = {
                TOTAL_ISSUED: 0,
                TOTAL_USED: 0,
                TOTAL_DEACTIVATED: 0,
                TOTAL_REMOVED: 1,
                TOTAL_DOWNLOADED: 0,
                TOTAL_EMAILED: 0,
                BATCH_REMOVED: 0,
                SUCCESS: true,
            }
            deleteFormElement.reset();
            return respData
        }

        const resp = await handleButtonAlertClickHelper(e,
            DELETE_CURRENT_CODE_BUTTON_ID,
            deleteCodeButtonSpinnerElement,
            alertAttributes,
            handleRemoveRecoveryCodeApiRequest)

        if (resp) {
            statsTotalCodesRemovedBoard.textContent = resp.TOTAL_REMOVED
        }

    }



}



/**
 * Handles the click event for the "regenerate code" button.
 * 
 * When clicked triggers a fetch API that allows the user to 
 * regenerate a set of new batch recovery codes. When new
 * codes are regenerated the old one becomes null and void
 * 
 * @param {Event} e - The click event triggered by the button.
 */
async function handleRegenerateCodeButtonClick(e) {

    const alertAttributes = {
        title: "Ready to get new codes?",
        text: "Doing this will remove your current codes. Are you sure you want to go ahead?",
        icon: "warning",
        cancelMessage: "No worries! Your codes are safe.",
        messageToDisplayOnSuccess: "Awesome! Your new recovery codes are ready.",
        confirmButtonText: "Yes, regenerate",
        denyButtonText: "No, keep my existing codes"
    }


    const handleGenerateCodeWithNoExpiryClickFetchAPI = () => {
        const respData = {
            TOTAL_ISSUED: 1,
            TOTAL_USED: 0,
            TOTAL_DEACTIVATED: 0,
            TOTAL_REMOVED: 0,
            TOTAL_DOWNLOADED: 0,
            TOTAL_EMAILED: 0,
            BATCH_REMOVED: 0,
            SUCCESS: true,
        }
        return respData;


    }
    const resp = await handleButtonAlertClickHelper(e,
        REGENERATE_BUTTON_ID,
        regenerateButtonSpinnerElement,
        alertAttributes,
        handleGenerateCodeWithNoExpiryClickFetchAPI
    )

    if (resp.SUCCESS) {
        statsTotalCodesIssuedBoard.textContent = resp.TOTAL_ISSUED;
        toggleElement(generateCodeSectionElement)
    }
}



/**
 * Handles the click event for the "email code" button.
 * 
 * When clicked triggers a fetch API that allows the user to 
 * email themselves their recovery code.
 * 
 * Note: The process can only be done once meaning 
 * @param {Event} e - The click event triggered by the button.
 */
async function handleEmailCodeeButtonClick(e) {


    const alertAttributes = {
        title: "Email codes?",
        text: "Would you like to email yourself the recovery codes?",
        icon: "info",
        cancelMessage: "No worries! Just make sure to copy or download the codes.",
        messageToDisplayOnSuccess: "Awesome! Your new recovery codes have been emailed.",
        confirmButtonText: "Yes, email me",
        denyButtonText: "No, don't email"
    }


    const handleEmailFetchApiSend = () => {
        console.log("Fetching data...");
        const respData = {
            TOTAL_ISSUED: 1,
            TOTAL_USED: 0,
            TOTAL_DEACTIVATED: 0,
            TOTAL_REMOVED: 0,
            TOTAL_DOWNLOADED: 0,
            TOTAL_EMAILED: 1,
            BATCH_REMOVED: 0,
            SUCCESS: true,
        }
        return respData;

    }
    const resp = await handleButtonAlertClickHelper(e, EMAIL_BUTTON_ID, emailButtonSpinnerElement, alertAttributes, handleEmailFetchApiSend)
    if (resp.SUCCESS) {
        statsTotalCodesEmailedBoard.textContent = resp.TOTAL_EMAILED
    }
    console.log(resp)
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
async function handlDeleteAllCodeButtonClick(e) {

    const alertAttributes = {
        title: "Delete All codes?",
        text: "This action will delete all your existing recovery codes. Would you like to proceed?",
        icon: "warning",
        cancelMessage: "No worries! Your codes are safe.",
        messageToDisplayOnSuccess: "All your recovery codes have been deleted.",
        confirmButtonText: "Yes, delete existing codes",
        denyButtonText: "No, don't delete my codes"
    }

    const handleDeleteAllCodeFetchApi = () => {
        console.log("Deleted all codes")
    }


    const handleDeleteAllCodesApiRequest = () => {
        console.log("Fetching data...");
        const respData = {
            TOTAL_ISSUED: 1,
            TOTAL_USED: 0,
            TOTAL_DEACTIVATED: 0,
            TOTAL_REMOVED: 1,
            TOTAL_DOWNLOADED: 0,
            TOTAL_EMAILED: 0,
            BATCH_REMOVED: 0,
            SUCCESS: true,
        }
        return respData;

    }
    const resp = await handleButtonAlertClickHelper(e,
        DELETE_ALL_CODES_BUTTON_ID,
        deleteAllCodeButtonSpinnerElement,
        alertAttributes,
        handleDeleteAllCodesApiRequest,
    )

    if (resp) {
        statsBatchCodesRemovedBoard.textContent = resp.TOTAL_REMOVED;
    }

}



/**
 * 
 * --------------------------------------------------------------------
 * Handles input field elements
 * --------------------------------------------------------------------
 * 
 *  
 * 
 * */


/**
 * Handles the click event on the expiry date inclusion checkbox.
 *
 * When the checkbox is toggled, this function shows or hides the
 * "add expiry days" input section in the form. This input allows
 * the user to specify how many days until the recovery code expires.
 *
 * If the checkbox is unchecked, recovery codes generated will
 * expire after the specified number of days.
 * If checked, recovery codes will be indefinite (no expiry).
 *
 * Additionally, it toggles the visibility of the generate button
 * based on the checkbox state.
 *
 * @param {Event} e - The event triggered by clicking the checkbox.
 * @returns {void}
 */
function handleIncludeExpiryDateCheckMark(e) {

    showSpinnerFor(excludeSpinnerLoaderElement, MILLI_SECONDS_BEFORE_DISPLAY);

    const excludeInputFieldCheckElement = e.target;


    if (excludeInputFieldCheckElement.checked) {
        daysToExpiryGroupWrapperElement.classList.add("d-none");
        generateButtonElement.classList.remove("d-none");
        return;
    }

    daysToExpiryGroupWrapperElement.classList.remove("d-none");
    generateButtonElement.classList.add("d-none");


}



/**
 * 
 * --------------------------------------------------------------------
 * Handles form submision section
 * --------------------------------------------------------------------
 * 
 *  
 * 
 * */



/**
 * Handles the submission event for the "Generate code" form.
 *
 * The function allows the user to generate a set of recovery
 * codes via a fetch API request when the form is submitted.
 *
 *
 * @param {Event} e - The submit event triggered by the form.
 * @returns {void}
 */
function handleGenerateCodeWithExpiryFormSubmission(e) {
    return handleFormSubmissionHelper(e, generateCodeWithExpiryFormElement, ["days-to-expiry"]);

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
function handleDeleteFormSubmission(e) {
    return handleFormSubmissionHelper(e, deleteFormElement, ["delete_code"]);

}





/**
 * Helper function that handles generic form submissions by validating the form
 * and extracting its data in a structured format.
 *
 *
 * This function is designed for reuse across multiple form submission scenarios
 * to centralise validation and data parsing logic.
 *
 * @param {Event} e - The submit event triggered by the form.
 * @param {HTMLFormElement} formElement - The form element being submitted.
 * @param {string[]} requiredFields - An array of field names that must be present in the form data.
 * @returns {Object|undefined} An object containing parsed form data if validation succeeds;
 *                              otherwise, undefined if validation fails.
 */
function handleFormSubmissionHelper(e, formElement, requiredFields) {

    if (!e || !e.target) {
        return;
    }

    checkIfHTMLElement(formElement, "Form Element");

    if (!Array.isArray(requiredFields)) {
        logError("handleFormSubmissionHelper", `The form required list must be an array. Expected an array but got type ${type(requiredFields)}`);
        return;
    }

    e.preventDefault();


    if (!formElement.checkValidity()) {
        formElement.reportValidity();
        return
    }

    const formData = new FormData(formElement);
    return parseFormData(formData, requiredFields);
}





/**
 * 
 * --------------------------------------------------------------------
 * Handles input helper function
 * --------------------------------------------------------------------
 * 
 *  
 * 
 * */

/**
 * A Helper function that processes input events for a text field by validating its length,
 * sanitising its content, converting it to uppercase, and formatting it with dashes.
 *
 * This function is intended to be called within other event handlers
 * to keep input field logic modular and reusable.
 *
 * @param {Event} e - The input event triggered by the text field.
 * @returns {void}
 */
function handleInputFieldHelper(e) {

    const inputField = e.target;

    if (!e || !e.target) {
        return;
    }

    if (inputField && inputField.validity.tooShort) {
        const charsNeeded = inputField.minLength - inputField.value.length;
        inputField.setCustomValidity(
            `Minimum length is ${inputField.minLength}. Please enter ${charsNeeded > 0 ? charsNeeded : 0} more character(s).`
        );
    } else {
        inputField.setCustomValidity(''); // reset
    }

    const LENGTH_PER_DASH = 4;

    e.target.value = sanitizeText(inputField.value, false, true).toUpperCase();
    applyDashToInput(e, LENGTH_PER_DASH);


}



/**
 * An ansync function that handles recovery code actions (generate with expiry, generate without expiry, or regenerate).
 *
 * This function centralizes the logic for showing confirmation alerts, toggling spinners,
 * sending a fetch request to the backend, and rendering the resulting codes to the UI once
 * it receives the codes from the fetch.
 * 
 * Note for security purpose there is no extra step between fetching the the raw
 * codes and rendering to the UI. As soon as the code is received it is rendered
 * immediately and it does not store the codes anywhere on the frontend.
 *
 * The specific behaviour is determined by the configuration object passed in.
 *
 * Args:
 *   options (Object): Configuration object.
 *   options.event (Event): The click event that triggered the action.
 *   options.button (HTMLElement): The button element that initiated the action.
 *   options.spinner (HTMLElement): The spinner element to show while the request is processing.
 *   options.alert (Object): Alert configuration for confirmation, including title, text,
 *       messages, and button labels.
 *   options.url (string): The API endpoint to call (e.g., generate with expiry, without expiry, regenerate).
 *
 * Returns:
 *   Promise<Object>: A response object containing:
 *     - SUCCESS (boolean): Whether the action completed successfully.
 *     - TOTAL_ISSUED (number): The total number of codes issued (if successful).
 *     - CODES (Array<string>): The generated or regenerated recovery codes.
 *     - ERROR (string): An error message if the action failed.
 *
 * Throws:
 *   Error: If the fetch request fails unexpectedly.
 */
async function handleRecoveryCodesAction({e,
                                        generateCodeBtn,
                                        generateCodeBtnSpinnerElement,
                                        alertAttributes,   
                                        url,
                                        daysToExpiry = null
                                        }) 
        {
        
        const body = {};

        if (daysToExpiry !== null && typeof daysToExpiry === "number") {
             body.daysToExpiry = daysToExpiry
        }
       

        const handleGenerateCodeFetchApi = async () => {
          
            const resp = await fetchData({
                url: url,
                csrfToken: getCsrfToken(),
                method: "POST",
                body: body,
            });

            return resp;
        }

        tableCoderSpinnerElement.style.display = "inline-block"
        toggleSpinner(tableCoderSpinnerElement);

        const resp = await handleButtonAlertClickHelper(e,
                                                        generateCodeBtn,
                                                        generateCodeBtnSpinnerElement,
                                                         alertAttributes,
                                                        handleGenerateCodeFetchApi
                                                       )

        if (resp.SUCCESS) {
          
            statsTotalCodesIssuedBoard.textContent = resp.TOTAL_ISSUED;
            toggleElement(generateCodeSectionElement);
            const isPopulated = populateTableWithUserCodes(resp.CODES);
           
            if (isPopulated) {
              markRecoveryCodesAsViewed();
            }
           return true;

        } else {
            messageContainerElement.classList.add("show");
            messageContainerElement.textContent = "Something went wrong and we couldn't generate your recovery codes"

            tableCoderSpinnerElement.style.display = "none";
            return false;
        }
}


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
async function handleButtonAlertClickHelper(e, buttonElementID, buttonSpinnerElement, alertAttributes = {}, func = null) {

    if (!(typeof alertAttributes === "object")) {
        logError("handleButtonAlertClickHelper", `The parameter alertAttributes is not an object. Expected an object but got type: ${typeof alertAttributes}`)
    }

    if (!(typeof buttonElementID === "string")) {
        logError("handleButtonAlertClickHelper", `The parameter buttonElementID is not an string. Expected a string but got type: ${typeof buttonElement}`)
    }

    if (func && !(typeof func === "function")) {
        logError("handleButtonAlertClickHelper", `The parameter func is not a function. Expected a function but got type: ${typeof func}`)
    }

    const buttonElement = e.target.closest("button");

    if (!buttonElement || buttonElement.tagName !== 'BUTTON' || buttonElement.id !== buttonElementID) {
        return;
    }

    toggleSpinner(buttonSpinnerElement);
    toggleButtonDisabled(buttonElement);

    await new Promise(requestAnimationFrame);

    try {
        const resp = await AlertUtils.showConfirmationAlert({
            title: alertAttributes.title,
            text: alertAttributes.text,
            icon: alertAttributes.icon,
            cancelMessage: alertAttributes.cancelMessage,
            messageToDisplayOnSuccess: alertAttributes.messageToDisplayOnSuccess,
            confirmButtonText: alertAttributes.confirmButtonText,
            denyButtonText: alertAttributes.denyButtonText
        });

        if (resp) {
            if (func) {
                return func()
            }
        }

        return resp;

    } finally {
        toggleSpinner(buttonSpinnerElement, false);
        toggleButtonDisabled(buttonElement, false)
    }


}


function toggleSideBarIcon(navIconElement) {

    if (navIconElement.id !== OPEN_NAV_BAR_HAMBURGERR_ICON && navIconElement.id !== CLOSE_NAV_BAR_ICON) {
        return;
    }

    let isNavOpen = true;

    if (navIconElement.id === OPEN_NAV_BAR_HAMBURGERR_ICON) {
        navIconElement.classList.add("rotate-360")
    }

    if (navIconElement.id === CLOSE_NAV_BAR_ICON) {
        isNavOpen = false;
        navIconElement.classList.add("rotate-360");
    }

    setTimeout(() => {

        if (isNavOpen) {
            navIconElement.classList.remove("rotate-360");
            navIconElement.style.display = "none";
            closeXIcon.style.display = "block";

            navigationIconContainerElement.style.height = "auto";
            recovryDashboardElement.style.marginTop = "400px";

            navigationIconContainerElement.classList.add("active")

        } else {

            navIconElement.classList.remove("rotate-360");
            navIconElement.style.display = "none";
            closeXIcon.style.display = "none";
            hamburgerOpenIcon.style.display = "block";
            navigationIconContainerElement.style.height = "0";
            recovryDashboardElement.style.marginTop = "65px";
            navigationIconContainerElement.classList.remove("active")


        }


    }, 500);
}



function toggleElement(element, hide = true) {
    if (hide) {
        element.classList.add("d-none");
        return
    }

    element.classList.remove("d-none");
}


function populateTableWithUserCodes(codes) {

   

    const tableObjectData = {
        classList: ["margin-top-lg"],
        id: "generated-codes-table",

    }

    const MILLI_SECONDS = 6000; // seconds is only for the message. It takes 5 seconds to make it journey up and down
    const colHeaders = ["status", "codes"];

    const tableElement = HTMLTableBuilder(colHeaders, codes, tableObjectData);
    codeTableElement.innerHTML = "";


    if (tableElement) {
        messageContainerElement.classList.add("show");
        messagePTag.textContent = "Your recovery codes are now ready...";


        setTimeout(() => {

            tableCoderSpinnerElement.style.display = "none"

            toggleSpinner(tableCoderSpinnerElement, false);
            codeTableElement.appendChild(tableElement);
            messageContainerElement.classList.remove("show");
            
            codeGenerationComplete();
        }, MILLI_SECONDS)

    }

    return true;
}


async function markRecoveryCodesAsViewed(url = "/auth/recovery-codes/viewed/") {
   try {
        await fetchData({
            url: url,
            csrfToken: getCsrfToken(),
            method: "POST",
            body: {}             // fetchData will handle stringifying and headers
        });
    } catch (error) {
        console.warn("Failed to mark codes as viewed:", error);
    }
}



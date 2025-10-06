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



// App-level imports
import { AlertUtils } from "../alerts.js";
import { updateBatchHistorySection } from "../batchCardsHistory/updateBatchHistorySection.js";
import { updateCurrentRecoveryCodeBatchCard } from "../batchCardsHistory/updateBatchHistorySection.js";
import { loadTestVerificationElements } from "../codesSetupVerifcation/handleTestSetup.js";
import { updateButtonFromConfig, buttons }   from "../generateCodeActionButtons.js";
import { sendPostFetchWithoutBody } from "../fetch.js";
import fetchData from "../fetch.js";
import { showTemporaryMessage } from "../messages/message.js";
import { getCsrfToken } from "../security/csrf.js";
import appStateManager from "../state/appStateManager.js";
import { showSpinnerFor, toggleSpinner, toggleElement, getOrFetchElement } from "../utils.js";


import { safeUIUpdate } from "../utils.js";

// Local imports
import messageContainerElement from "./appMessages.js";
import { handleButtonAlertClickHelper } from "./handleButtonAlertClicker.js";
import { handleFormSubmissionHelper } from "./formUtils.js";
import { populateTableWithUserCodes } from "./tableUtils.js";
import { generaterecoveryBatchSectionElement, recoveryBatchSectionElement } from "../batchCardsHistory/batchCardElements.js";
import { markCurrentCardBatchAsViewed } from "../batchCardsHistory/updateBatchHistorySection.js";



// The elemnts are not checked
const daysToExpiryGroupWrapperElement = document.getElementById("days-to-expiry-group");
const codeActionButtons = document.getElementById("code-actions");

// spinner elements
// Loader element IDs
const GENERATE_LOADER_ID = "generate-code-loader";
const GENERATE_CODE_WITHOUT_EXPIRY_LOADER_ID = "generate-code-without-expiry-loader";
const EXCLUDE_EXPIRY_LOADER_ID = "exclude-expiry-loader";
const TABLE_LOADER_ID = "table-loader";
const EMAIL_BUTTON_ID = "email-code-btn";
const DOWNLOAD_CODE_BTN_ID = "download-code-btn";

// Loader elements
let generateCodeWithExirySpinnerElement = document.getElementById(GENERATE_LOADER_ID);
let generateCodeWithNoExpirySpinnerElement = document.getElementById(GENERATE_CODE_WITHOUT_EXPIRY_LOADER_ID);
let excludeSpinnerLoaderElement = document.getElementById(EXCLUDE_EXPIRY_LOADER_ID);
let tableCoderSpinnerElement = document.getElementById(TABLE_LOADER_ID);
let emailButtonElement            = document.getElementById(EMAIL_BUTTON_ID);
let downloadButtonElement         = document.getElementById(DOWNLOAD_CODE_BTN_ID)

// button elements
const generateButtonElement = document.getElementById("generate-code-button-wrapper");

// forms elements
const generateCodeWithExpiryFormElement = document.getElementById("generate-form-code-with-expiry");
const dynamicTestFormSetupElement = document.getElementById("dynamic-form-setup");
const verifyTestFormContainer = document.getElementById("verify-form-container");


function handleTableSpinnerElements() {
    tableCoderSpinnerElement.style.display = "inline-block";
    toggleSpinner(tableCoderSpinnerElement);
}


function resetEmailButton() {
    const msg = "Click the button to email your code"
    resetButtonsHelper(emailButtonElement,
                        EMAIL_BUTTON_ID,
                        buttons.emailCode,
                        msg,
                       

    )
}


function resetDownloadButton() {
    const msg = "Click the button to download your code"
    resetButtonsHelper(downloadButtonElement,
                        DOWNLOAD_CODE_BTN_ID,
                         buttons.downloadCode,
                        msg,
                       
    )
}


function resetButtonsHelper(buttonElement, buttonID, buttonNewState, buttonMsg) {
    buttonElement = getOrFetchElement(buttonElement, buttonID);
    if (!buttonElement) return;

    
    // Check that the config is valid
    if (!buttonNewState || !buttonNewState.button || !buttonNewState.button.buttonClassList) {
        console.warn(
            `Invalid button config passed for button with ID "${buttonID}".`,
            buttonNewState,
        );
        return;
    }

    // Check that buttonMsg is a string
    if (typeof buttonMsg !== "string") {
        console.warn(
            `Button message should be a string for button with ID "${buttonID}".`,
            buttonMsg
        );
        buttonMsg = "";
    }

    // safe update
    updateButtonFromConfig(buttonElement, buttonNewState, buttonMsg);
    
}

/**
 * Handles the click event for the "Generate Code" button.
 * 
 * Intended to generate recovery codes on the backend via the Fetch API.
 * 
 * @param {Event} e - The click event triggered by the button.
 */
export async function handleGenerateCodeWithExpiryClick(e, generateButtonID) {

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


        const resp = await handleRecoveryCodesAction({
            e: e,
            generateCodeBtn: generateButtonID,
            generateCodeBtnSpinnerElement: getOrFetchElement(generateCodeWithExirySpinnerElement, GENERATE_LOADER_ID),
            alertAttributes: alertAttributes,
            url: "/auth/recovery-codes/generate-with-expiry/",
            daysToExpiry: daysToExpiry,

        })

        return resp;


    }

}




/**
 * Handles the click event for the "Generate Code" button.
 * 
 * Intended to generate recovery codes on the backend via the Fetch API.
 * 
 * @param {Event} e - The click event triggered by the button.
 */
export async function handleGenerateCodeWithNoExpiryClick(e, generateCodeButtonID) {

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
        e: e,
        generateCodeBtn: generateCodeButtonID,
        generateCodeBtnSpinnerElement: getOrFetchElement(generateCodeWithNoExpirySpinnerElement, GENERATE_CODE_WITHOUT_EXPIRY_LOADER_ID),
        alertAttributes: alertAttributes,
        url: "/auth/recovery-codes/generate-without-expiry/",

    })

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
export async function handleRegenerateCodeButtonClick(e, regenerateButtonID, alertMessage) {

    const alertAttributes = {
        title: "Ready to get new codes?",
        text: "Doing this will remove your current codes. Are you sure you want to go ahead?",
        icon: "warning",
        cancelMessage: "No worries! Your codes are safe.",
        messageToDisplayOnSuccess: `
                Great! Your codes are being generated in the background and will be displayed in View Generated Codes section once ready.
                You can continue using the app while we prepare them.
                We’ll notify you once they’re ready.
                Please, don't close the page.
            `,
        confirmButtonText: "Yes, regenerate",
        denyButtonText: "No, keep my existing codes"
    }

    if (!alertMessage) {
        toggleElement(alertMessage);

    }

    return handleRecoveryCodesAction({
        e: e,
        generateCodeBtn: regenerateButtonID,
        generateCodeBtnSpinnerElement: generateCodeWithNoExpirySpinnerElement,
        alertAttributes: alertAttributes,
        url: "/auth/recovery-codes/regenerate/",

    })


}




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
export function handleIncludeExpiryDateCheckMark(e, milliseconds = 1000) {

    showSpinnerFor(getOrFetchElement(excludeSpinnerLoaderElement, EXCLUDE_EXPIRY_LOADER_ID), milliseconds);

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
 * Handles the UI updates after successfully generating recovery codes.
 *
 * This function performs the following steps:
 * 1. Toggles the generate recovery batch section visibility.
 * 2. Populates the user codes table and exits early if there are no codes.
 * 3. Marks the generated codes as viewed on the backend.
 * 4. Updates the batch history section with the latest batch information.
 * 5. Hides code action buttons and updates the app state to indicate code generation is complete.
 * 6. Optionally shows the verification form if the user has not completed setup.
 * 7. Hides the process message after a predefined delay.
 */
async function handleCanGenerateCodeSuccessUI(resp) {

    toggleElement(generaterecoveryBatchSectionElement);
    toggleElement(codeActionButtons);

    const isPopulated   = populateTableWithUserCodes(resp.CODES);
    const MILLI_SECONDS = 1000;
  
    if (isPopulated) {

        const resp = await sendPostFetchWithoutBody("/auth/recovery-codes/viewed/", "Failed to mark code as viewed ");
        if (resp && resp.SUCCESS) {
            markCurrentCardBatchAsViewed();
        }
     
        updateBatchHistorySection(recoveryBatchSectionElement, resp.BATCH, resp.ITEM_PER_PAGE);

        if (appStateManager.isRequestCodeGenerationActive()) {           
          
            setTimeout(() => {
                resetEmailButton();
                resetDownloadButton();
            }, MILLI_SECONDS);
        } else {
            toggleElement(codeActionButtons, false);
        }

        appStateManager.setCodeGeneration(false);
        handleInitializeFirstTimeVerificationTest(resp);
     

    }

    return true;
}



/**
 * Initializes the verification test setup for users running it for the first time.
 *
 * If the user has not completed the initial setup (`HAS_COMPLETED_SETUP` is false):
 *   - Displays the dynamic verification form if the static form container is hidden.
 *   - Loads additional elements required for the verification test.
 *
 * @param {Object} resp - The server response object containing user setup status.
 * @param {boolean} resp.HAS_COMPLETED_SETUP - Indicates whether the user has completed the setup.
 */
function handleInitializeFirstTimeVerificationTest(resp) {
    if (!resp.HAS_COMPLETED_SETUP) {

        if (!verifyTestFormContainer) {
            console.log("The static verify form is hidden due to Django if-statement; displaying dynamic form instead");
            toggleElement(dynamicTestFormSetupElement, false);
        }

        loadTestVerificationElements();
    }
}



/**
 * Handles the UI response when code generation fails.
 *
 * Displays an error message to the user for a specified duration.
 *
 * @param {number} [milliseconds=5000] - Duration to show the error message in milliseconds.
 * @param {string} [message="Oops, something went wrong and your request wasn't processed"] - Error message to display.
 */
function handleCannotGenerateCodeError(milliseconds = 5000, message = "OOps, something went wrong and your request wasn't processed") {
    handleGenerateBaseMessage(message, milliseconds);
}


/**
 * Handles the UI response when code generation fails, using a backend response object.
 *
 * Displays an error message from the server for a specified duration.
 *
 * @param {Object} resp - Response object from the backend.
 * @param {string} resp.MESSAGE - Error message returned from the server.
 * @param {number} [milliseconds=5000] - Duration to show the error message in milliseconds.
 */
function handleCannotGenerateCodeUI(resp, milliseconds = 5000) {
    handleGenerateBaseMessage(resp.MESSAGE, milliseconds);
}




/**
 * Handles the UI response when a code generation action is cancelled by the user.
 *
 * Displays a cancellation message using the base message handler.
 *
 * @param {string} [message="No, codes were generated, since the action was cancelled"] - Message to display to the user.
 */
function handleCancelMessage(message = "No, codes were generated, since the action was cancelled") {
    handleGenerateBaseMessage(message = message);
}



/**
 * Displays a temporary message to the user and updates UI elements accordingly.
 *
 * Hides the table spinner, toggles its visibility, and resets the app state after a delay.
 *
 * @param {string} message - The message to display.
 * @param {number} [milliseconds=5000] - Duration in milliseconds to display the message.
 */
function handleGenerateBaseMessage(message, milliseconds = 5000) {
    showTemporaryMessage(messageContainerElement, message);

    tableCoderSpinnerElement = getOrFetchElement(tableCoderSpinnerElement, TABLE_LOADER_ID);
    tableCoderSpinnerElement.style.display = "none";
    toggleSpinner(tableCoderSpinnerElement, false);

    setTimeout(() => {
        appStateManager.setCodeGeneration(false);
        return false;

    }, milliseconds)
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
async function handleRecoveryCodesAction({ e,
    generateCodeBtn,
    generateCodeBtnSpinnerElement,
    alertAttributes,
    url,
    daysToExpiry = null
}) {
    const body = {};

    if (daysToExpiry !== null && typeof daysToExpiry === "number") {
        body.daysToExpiry = daysToExpiry;
    }

    body.forceUpdate = true;

    toggleElement(generaterecoveryBatchSectionElement);
    toggleElement(codeActionButtons);

    const handleGenerateCodeFetchApi = async () => {

        const resp = await fetchData({
            url: url,
            csrfToken: getCsrfToken(),
            method: "POST",
            body: body,
        });

        return resp;
    }

    handleTableSpinnerElements();
   
    const resp = await handleButtonAlertClickHelper(e,
        generateCodeBtn,
        generateCodeBtnSpinnerElement,
        alertAttributes,
        handleGenerateCodeFetchApi
    )

    // if no action was perform e.g cancelled, show the buttons
    if (!resp) {
        handleCancelMessage();
        toggleElement(codeActionButtons, false);
        return;
    }

    if (resp.SUCCESS) {

        if (resp.CAN_GENERATE) {

            handleCanGenerateCodeSuccessUI(resp);

        } else {
            handleCannotGenerateCodeUI(resp);

        }

    } else {
        handleCannotGenerateCodeError();

    }

    toggleElement(codeActionButtons, false);
    appStateManager.setCodeGeneration(false);

   
}



/**
 * Displays a success or informational alert based on the response data
 * and updates the relevant recovery code batch field if the operation was successful.
 *
 * @param {Object} data - Response object from the backend.
 * @param {string} data.ALERT_TEXT - The alert title text from the server.
 * @param {string} data.MESSAGE - The alert message content from the server.
 * @param {string} successCompareMessage - The string to compare against ALERT_TEXT to determine a success.
 * @param {string} fieldName - The field name in the recovery code batch card to update on success.
 */
function handleSuccessOperationAlertAndUpdate(data, successCompareMessage, fieldName) {
    const icon = data.ALERT_TEXT === successCompareMessage ? "success" : "info";
   
    AlertUtils.showAlert({
        title: data.ALERT_TEXT,
        text: data.MESSAGE,
        icon: icon,
        confirmButtonText: "Ok"
    });

    if (icon === "success") {
        updateCurrentRecoveryCodeBatchCard(fieldName);
    }
}




/**
 * Displays an error alert when a code operation fails.
 *
 * Uses the backend response data if available, otherwise defaults to a generic message.
 *
 * @param {Object} [data] - Optional response object from the backend.
 * @param {string} [data.ALERT_TEXT] - Alert title text from the server.
 * @param {string} [data.MESSAGE] - Alert message content from the server.
 */
function handleFailureOperationAlertAndUpdate() {
    AlertUtils.showAlert({
        title: data.ALERT_TEXT || "Code not valid",
        text: data.MESSAGE || "The code entered is no longer valid",
        icon: "error",
        confirmButtonText: "Ok"
    });
    return;
}



/**
 * Displays an error alert when an invalid code is detected.
 *
 * This is used for general validation errors where the code entered is not recognized.
 */
function handleErrorOperationAlertAndUpdate() {
    AlertUtils.showAlert({
        title: "The code is invalid",
        text: "The code entered is an invalid code",
        icon: "error",
        confirmButtonText: "Ok"
    });
    return;
}


/**
 * Displays a standardised alert for recovery code operations (e.g., deactivate, delete).
 *
 * The function determines whether to show a ✅ success, ℹ️ info, or ❌ error alert
 * based on the operation outcome and the expected success message. It also increments
 * the field corresponding card batch value by one. The field increment depends 
 * on the form calling it. For example, if is being called by the `invalidate form` or `
 * `delete code form`
 *
 * @param {Object} data - The response data object returned from the backend.
 * @param {boolean} data.OPERATION_SUCCESS - Indicates whether the operation succeeded.
 * @param {string} data.ALERT_TEXT - A short alert title (shown as the modal heading).
 * @param {string} data.MESSAGE - The main message displayed in the alert body.
 * @param {string} expectedSuccessMessage - The success message that determines
 *        whether the alert should use a "success" (✅ green tick) or "info" (ℹ️ icon).
 *
 * Example:
 * handleRecoveryCodeAlert(data, "Code successfully deactivated");
 * handleRecoveryCodeAlert(data, "Code successfully deleted");
 */
export function handleRecoveryCodeAlert(data, successCompareMessage, fieldName) {

    if (data && Object.hasOwn(data, "SUCCESS")) {

        if (data.OPERATION_SUCCESS) {
            return handleSuccessOperationAlertAndUpdate(data, successCompareMessage, fieldName);
        }

        return handleFailureOperationAlertAndUpdate();

    }

    return handleErrorOperationAlertAndUpdate();


}





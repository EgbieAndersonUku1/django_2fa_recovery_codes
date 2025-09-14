import appStateManager from "../state/appStateManager.js";
import { showSpinnerFor, toggleSpinner, toggleElement } from "../utils.js";
import { showTemporaryMessage } from "../messages/message.js";
import { getCsrfToken } from "../security/csrf.js";
import { sendPostFetchWithoutBody } from "../fetch.js";
import { handleFormSubmissionHelper } from "./formUtils.js";


import { handleButtonAlertClickHelper } from "./handleButtonAlertClicker.js";
import { updateBatchHistorySection } from "../batchCardsHistory/updateBatchHistorySection.js";
import { updateCurrentRecoveryCodeBatchCard } from "../batchCardsHistory/updateBatchHistorySection.js";
import { populateTableWithUserCodes } from "./tableUtils.js";
import messageContainerElement from "./appMessages.js";

import { AlertUtils } from "../alerts.js";
import fetchData from "../fetch.js";


// Elements
const daysToExpiryGroupWrapperElement = document.getElementById("days-to-expiry-group");
const generaterecoveryBatchSectionElement = document.getElementById("generate-code-section");
const recoveryBatchSectionElement = document.getElementById("static-batch-cards-history")

// spinner elements
const generateCodeWithExirySpinnerElement = document.getElementById("generate-code-loader");
const generateCodeWithNoExpirySpinnerElement = document.getElementById("generate-code-without-expiry-loader");
const excludeSpinnerLoaderElement = document.getElementById("exclude-expiry-loader");
const tableCoderSpinnerElement = document.getElementById("table-loader");

// button elements
const generateButtonElement = document.getElementById("generate-code-button-wrapper");


// forms elements
const generateCodeWithExpiryFormElement = document.getElementById("generate-form-code-with-expiry");
const dynamicTestFormSetupElement = document.getElementById("dynamic-form-setup")




// Stats display board
const statsTotalCodesIssuedBoard = document.getElementById("stat__total_codes_issued")


// constants
const MILLI_SECONDS_BEFORE_DISPLAY = 500;
let alertMessage;



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
            generateCodeBtnSpinnerElement: generateCodeWithExirySpinnerElement,
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
        generateCodeBtnSpinnerElement: generateCodeWithNoExpirySpinnerElement,
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
export async function handleRegenerateCodeButtonClick(e) {

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

    toggleElement(alertMessage)

    handleRecoveryCodesAction({
        e: e,
        generateCodeBtn: REGENERATE_BUTTON_ID,
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
export function handleIncludeExpiryDateCheckMark(e) {

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


function handleCanGenerateCodeSuccessUI(resp) {
    statsTotalCodesIssuedBoard.textContent = resp.TOTAL_ISSUED;
    toggleElement(generaterecoveryBatchSectionElement);

    const isPopulated = populateTableWithUserCodes(resp.CODES);

    if (isPopulated) {

        sendPostFetchWithoutBody("/auth/recovery-codes/viewed/",
            "Failed to mark code as viewed "
        );

        updateBatchHistorySection(recoveryBatchSectionElement, resp.BATCH, resp.ITEM_PER_PAGE);

        appStateManager.setCodeGeneration(false);

        console.log(resp)
        // show the optional verification form
        // toggleElement(testSetupFormContainerElement, false);
        if (!resp.HAS_COMPLETED_SETUP) {
            toggleElement(dynamicTestFormSetupElement, false);
            loadTestVerificationElements();
        }

    }


    return true;
}


function handleCannotGenerateCodeUI(resp, milliseconds = 5000) {

    showTemporaryMessage(messageContainerElement, resp.MESSAGE);

    tableCoderSpinnerElement.style.display = "none";
    toggleSpinner(tableCoderSpinnerElement, false);

    setTimeout(() => {
        appStateManager.setCodeGeneration(false);
        return false;

    }, milliseconds)
}


function handleCannotGenerateCodeError(milliseconds = 5000) {
    const DEFAULT_MESSAGE = "Hang on we are trying to process your request.."

    showTemporaryMessage(messageContainerElement, DEFAULT_MESSAGE)
    tableCoderSpinnerElement.style.display = "none";
    toggleSpinner(tableCoderSpinnerElement, false);

    setTimeout(() => {

        appStateManager.setCodeGeneration(false)
        messageContainerElement.classList.remove("show");
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

    if (resp && resp.SUCCESS) {
        return resp.CAN_GENERATE ? handleCanGenerateCodeSuccessUI(resp) : handleCannotGenerateCodeUI(resp);
    }

    return handleCannotGenerateCodeError()

}


function handleSuccessOperationAlertAndUpdate(data, successCompareMessage, fieldName) {
    const icon = data.ALERT_TEXT === successCompareMessage ? "success" : "info";

    AlertUtils.showAlert({
        title: data.ALERT_TEXT,
        text: data.MESSAGE,
        icon: icon,
        confirmButtonText: "Ok"
    });

    if (icon === "success") {
        updateCurrentRecoveryCodeBatchCard(recoveryBatchSectionElement, fieldName);
    }
}


function handleFailureOperationAlertAndUpdate() {
    AlertUtils.showAlert({
        title: data.ALERT_TEXT || "Code not valid",
        text: data.MESSAGE || "The code entered is no longer valid",
        icon: "error",
        confirmButtonText: "Ok"
    });
    return;
}


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





/**
 * dashboardHelper.js
 *
 * This file contains helper functions specific to dashboard.js.
 * 
 * Purpose:
 * - Keep dashboard.js clean and uncluttered.
 * - Provide functionality that is specific to the dashboard workflow.
 * 
 * Notes:
 * - Not a general-purpose utils.js.
 * - Functions here are intended to work only with dashboard.js.
 * - Can be expanded in the future with more dashboard-specific helpers.
 */



import { toggleSpinner, toggleButtonDisabled, getNthChildNested, checkIfHTMLElement, addChildWithPaginatorLimit } from "./utils.js";
import { logError } from "./logger.js";
import { AlertUtils } from "./alerts.js";
import { generateRecoveryCodesSummaryCard } from "./generateBatchHistoryCard.js";


const dynamicBatchSpinnerElement = document.getElementById("dynamic-batch-loader");

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
        let resp;
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
        } else {
            resp = true;
        }
        if (resp) {
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




export function incrementRecoveryCardField(cardBatchElement, fieldSelector, MILLI_SECONDS = 6000) {
    if (!checkIfHTMLElement(cardBatchElement)) {
        warnError(
            "incrementRecoveryCardField",
            `Expected a field p Element. Got object with type ${typeof cardBatchElement}`
        );
        return; // Exit if not a valid element
    }

    const PElements = cardBatchElement.querySelectorAll('.card-head .info-box .value p');
    
    for (const pElement of PElements) {
        // Only increment fields with the correct class

        if (pElement.classList.contains(fieldSelector)) {
            const currentValue = parseInt(pElement.textContent || "0", 10);
            pElement.textContent = currentValue + 1;
        
            pElement.classList.add("text-green", "bold", "highlight");
            
            setTimeout(() => {
                pElement.classList.remove("highlight");
            }, MILLI_SECONDS);

            break;
        }
    }
}



export function updateCurrentRecoveryCodeBatchCard(sectionElement, fieldToUpdate, tagName="div", classSelector="card-head") {
    const currentCardBatch = getNthChildNested(sectionElement, 1, tagName, classSelector);

    switch(fieldToUpdate) {
        case "invalidate":
            incrementRecoveryCardField(currentCardBatch, "number_invalidated");
            break;
         case "delete":
            incrementRecoveryCardField(currentCardBatch, "number_removed");
            break;
        
    }
   
}



export function updateBatchHistorySection(sectionElement,
                                         batch, 
                                         batchPerPage = 5, 
                                         milliSeconds = 7000,
                                         tagName="div",
                                         classSelector="card-head",
                                         batchNumberToUpdate = 2,

                                        ) {
    const newBatchCard = generateRecoveryCodesSummaryCard(batch);
    
    let previousBatchCard;

    dynamicBatchSpinnerElement.style.display = "inline-block";
    toggleSpinner(dynamicBatchSpinnerElement);

    setTimeout(() => {
        addChildWithPaginatorLimit(sectionElement, newBatchCard, batchPerPage);

        previousBatchCard = getNthChildNested(
            sectionElement,
            batchNumberToUpdate,
            tagName,
            classSelector,
        );
        markCardAsDeleted(previousBatchCard);

        toggleSpinner(dynamicBatchSpinnerElement, false);
    }, milliSeconds);
}



export function markCardAsDeleted(cardElement) {

    if (cardElement === null) return;

    const statusElements = cardElement.querySelectorAll('.card-head .info-box .value p');
    if (!statusElements.length) return;


    for (const pElement of statusElements) {
        if (pElement.classList.contains('status')) {
            pElement.textContent = "Deleted";
            pElement.classList.remove("text-green");
            pElement.classList.add("text-red", "bold");
            break;
        }
    }
}

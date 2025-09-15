import { handleRecoveryCodeAlert } from "./handleCodeGeneration.js";
import { handleFormSubmissionHelper } from "./formUtils.js";
import { handleButtonAlertClickHelper } from "./handleButtonAlertClicker.js";
import fetchData from "../fetch.js";
import { getCsrfToken } from "../security/csrf.js";
import { checkIfHTMLElement } from "../utils.js";
import { toggleElement } from "../utils.js";
import { AlertUtils } from "../alerts.js";
import { doNothing } from "../utils.js";

export const deleteInputFieldElement    = document.getElementById("delete-code-input");
const testSetupFormContainerElement     = document.getElementById("dynamic-verify-form-container");

const deleteAllCodeButtonSpinnerElement = document.getElementById("delete-all-code-loader");
const deleteCodeButtonSpinnerElement    = document.getElementById("delete-current-code-loader");
const deleteFormElement                 = document.getElementById("delete-form");


deleteFormElement.addEventListener("submit", handleDeleteFormSubmission);
deleteFormElement.addEventListener("input", handleDeleteFormSubmission);
deleteFormElement.addEventListener("blur", handleDeleteFormSubmission);

export default deleteFormElement;




function toggleCodeUIElementsOff(codeActionButtons, tableCodes) {
    toggleElement(codeActionButtons);
    toggleElement(tableCodes);
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

        handleRecoveryCodeAlert(data, "Code successfully deleted", "delete");
        deleteFormElement.reset()

    };


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
export async function handleDeleteAllCodeButtonClick(e,  deleteAllCodesButtonID, alertMessage) {

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

        const resp = await fetchData({url: "/auth/recovery-codes/mark-batch-as-deleted/",
                                      csrfToken: getCsrfToken(),
                                      method: "POST",
                                      body: {forceUpdate: true},
                                     });

        return resp;

    }

    const resp = await handleButtonAlertClickHelper(e,
                        deleteAllCodesButtonID,
                        deleteAllCodeButtonSpinnerElement,
                        alertAttributes,
                        handleDeleteAllCodesApiRequest,
                    )

    if (resp && resp.SUCCESS) {

        const {codeActionButtons, tableCodes} = getDynamicCodeUIElements();
        
        if (!(checkIfHTMLElement(codeActionButtons) && checkIfHTMLElement(tableCodes))) {
            warnError("handleDeleteAllCodeButtonClick", "The button container element wasn't found");
            return;
        }

       
        toggleCodeUIElementsOff(codeActionButtons, tableCodes);
        showSuccessDeleteAlert();
        toggleAlertAndFormElements();

        try {
            toggleElement(testSetupFormElement)
        } catch (error) {
            doNothing()
            }

        }    

}

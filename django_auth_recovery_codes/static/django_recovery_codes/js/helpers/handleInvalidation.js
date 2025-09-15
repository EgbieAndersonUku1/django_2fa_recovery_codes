import { handleRecoveryCodeAlert } from "./handleCodeGeneration.js";
import { handleButtonAlertClickHelper } from "./handleButtonAlertClicker.js";
import { handleFormSubmissionHelper } from "./formUtils.js";
import fetchData from "../fetch.js";
import { getCsrfToken } from "../security/csrf.js";


const invalidateSpinnerElement            = document.getElementById("invalidate-code-loader");
export const invalidateInputFieldElement  = document.getElementById('invalidate-code-input');
const invalidateFormElement               = document.getElementById("invalidate-form");
const INVALIDATE_CODE_BTN_ID              = "invalidate-code-btn";

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
    // console.log(data)
    const data = await handleButtonAlertClickHelper(
        e,
        INVALIDATE_CODE_BTN_ID,
        invalidateSpinnerElement,
        alertAttributes,
        handleInvalidateCodeFetchAPI
    );


    handleRecoveryCodeAlert(data, "Code successfully deactivated", "invalidate");

    invalidateFormElement.reset();
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

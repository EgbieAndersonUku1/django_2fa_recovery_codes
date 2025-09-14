import { handleRecoveryCodeAlert } from "./handleCodeGeneration.js";
import { handleFormSubmissionHelper } from "./formUtils.js";



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






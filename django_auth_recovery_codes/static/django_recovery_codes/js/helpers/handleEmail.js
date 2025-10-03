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



import messageContainerElement                   from "./appMessages.js";
import EnqueuedMessages                           from "../messages/enqueueMessages.js";
import { handleButtonAlertClickHelper }           from "./handleButtonAlertClicker.js";
import { sendPostFetchWithoutBody }               from "../fetch.js";
import { updateButtonFromConfig, buttonStates }   from "../generateCodeActionButtons.js";
import { toggleButtonDisabled, getOrFetchElement} from "../utils.js";
import { showTemporaryMessage }                   from "../messages/message.js";
import { markCurrentCardBatchAsEmailed }          from "../batchCardsHistory/updateBatchHistorySection.js";


const EMAIL_LOADER_ID           = "email-code-loader";
let emailButtonSpinnerElement   = document.getElementById(EMAIL_LOADER_ID); // Dynamic, doesn't exist at runtime
const enqueuedMessages          = new EnqueuedMessages();







/**
 * Handles the click event for the "email code" button.
 * 
 * When clicked triggers a fetch API that allows the user to 
 * email themselves their recovery code.
 * 
 * Note: The process can only be done once meaning 
 * @param {Event} e - The click event triggered by the button.
 */
export async function handleEmailCodeeButtonClick(e, emailButtonID) {

    const alertAttributes = {
        title: "Email Recovery Codes?",
        text: "Would you like to email yourself the recovery codes?",
        icon: "info",
        cancelMessage: "No worries! Just make sure to copy or download the codes.",
        messageToDisplayOnSuccess: "Awesome! Your recovery codes are on their way. We’ll notify you once the email is sent.",
        confirmButtonText: "Yes, email me",
        denyButtonText: "No, thanks"
    }

    const handleEmailFetchApiSend = async () => {
            const url = "/auth/recovery-codes/email/";
            return await sendPostFetchWithoutBody(url, "The email wasn't sent")
    }

    const resp = await handleButtonAlertClickHelper(e,
                                                    emailButtonID,
                                                    getOrFetchElement(emailButtonSpinnerElement, EMAIL_LOADER_ID),
                                                    alertAttributes, 
                                                    handleEmailFetchApiSend
                                                    );

    if (resp === undefined) {
        showTemporaryMessage("Something went wrong and the email wasn't sent");

        return;
    }
   
    resp && resp.SUCCESS ? handleEmailSuccessMessageUI(e, resp) : handleEmailFailureMessageUI(resp);
   
    return true;

}


/**
 * Handles the UI updates after successfully emailing recovery codes.
 *
 * - Updates the email button state.
 * - Disables the button temporarily.
 * - Enqueues and displays the success message.
 * - Marks the current recovery code batch as emailed.
 * - Hides the processing message after a short delay.
 *
 * @param {Event} e - The click event from the email button.
 * @param {Object} resp - The backend response object containing a message.
 * @param {string} resp.MESSAGE - Message to display to the user.
 */
function handleEmailSuccessMessageUI(e, resp) {

    const btn            = e.target.closest("button");
    const MILLI_SECONDS  = 2000;
    updateButtonFromConfig(btn, buttonStates.emailed, "You have already emailed yourself this code");
    toggleButtonDisabled(btn);

    enqueuedMessages.addMessage(resp.MESSAGE);
    enqueuedMessages.showEnqueuedMessages(messageContainerElement);
    markCurrentCardBatchAsEmailed();

 
}


/**
 * Handles the UI updates when emailing recovery codes fails.
 *
 * - Displays the backend failure message if provided.
 * - Hides the processing message.
 *
 * @param {Object} [resp] - The backend response object.
 * @param {string} [resp.MESSAGE] - The error message returned from the server.
 */
function handleEmailFailureMessageUI(resp) {
    if (resp) {
        enqueuedMessages.addMessage(resp.MESSAGE);
        enqueuedMessages.showEnqueuedMessages(messageContainerElement);
    }
 
}
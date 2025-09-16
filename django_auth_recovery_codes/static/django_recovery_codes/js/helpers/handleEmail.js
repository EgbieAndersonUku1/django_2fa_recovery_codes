import messageContainerElement                  from "./appMessages.js";
import EnqueuedMessages                         from "../messages/enqueueMessages.js";
import { handleButtonAlertClickHelper }         from "./handleButtonAlertClicker.js";
import { sendPostFetchWithoutBody }             from "../fetch.js";
import { updateButtonFromConfig, buttonStates } from "../generateCodeActionButtons.js";
import { toggleButtonDisabled }                 from "../utils.js";
import { toggleProcessMessage }                 from "./handleButtonAlertClicker.js";
import { showTemporaryMessage }                 from "../messages/message.js";


const emailButtonSpinnerElement = document.getElementById("email-code-loader");
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
                                                    emailButtonSpinnerElement,
                                                    alertAttributes, 
                                                    handleEmailFetchApiSend
                                                    );

    if (resp === undefined) {
        showTemporaryMessage("Something went wrong and the email wasn't sent");
        toggleProcessMessage(false);
        return;
    }
   
    resp && resp.SUCCESS ? handleEmailSuccessMessageUI(e, resp) : handleEmailFailureMessageUI(resp);
   
    return true;

}


function handleEmailSuccessMessageUI(e, resp) {

    const btn = e.target.closest("button");
    updateButtonFromConfig(btn, buttonStates.emailed, "You have already emailed yourself this code");
    toggleButtonDisabled(btn);

    enqueuedMessages.addMessage(resp.MESSAGE);
    enqueuedMessages.showEnqueuedMessages(messageContainerElement);

    setTimeout(() => {
        toggleProcessMessage(false)
    }, 2000)
   
}


function handleEmailFailureMessageUI(resp) {
    if (resp) {
        enqueuedMessages.addMessage(resp.MESSAGE);
        enqueuedMessages.showEnqueuedMessages(messageContainerElement);
    }
 
    toggleProcessMessage(false)
}
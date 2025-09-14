const emailButtonSpinnerElement = document.getElementById("email-code-loader");



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

    if (resp.SUCCESS) {

        const btn = e.target.closest("button");
        updateButtonFromConfig(btn, buttonStates.emailed, "You have already emailed yourself this code");
        toggleButtonDisabled(btn);

        enqueueMessages.push(resp.MESSAGE);
        showEnqueuedMessages(enqueueMessages, messageContainerElement)


    } else {
        enqueueMessages.push(resp.MESSAGE)
        showEnqueuedMessages(enqueueMessages, messageContainerElement)

    }

}

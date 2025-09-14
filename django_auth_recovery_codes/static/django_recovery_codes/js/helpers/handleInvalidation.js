

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
async function handleInvalidateButtonClick(e) {
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
        INVALIDATE_CODE_BTN,
        invalidateSpinnerElement,
        alertAttributes,
        handleInvalidateCodeFetchAPI
    );

    console.log(data)
    handleRecoveryCodeAlert(data, "Code successfully deactivated", "invalidate");

    invalidateFormElement.reset();
}



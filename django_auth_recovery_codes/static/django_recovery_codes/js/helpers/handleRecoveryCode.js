

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
     
        if (resp.CAN_GENERATE) {
            statsTotalCodesIssuedBoard.textContent = resp.TOTAL_ISSUED;
            toggleElement(generaterecoveryBatchSectionElement);

            const isPopulated = populateTableWithUserCodes(resp.CODES);

            if (isPopulated) {
                sendPostFetchWithoutBody("/auth/recovery-codes/viewed/",
                    "Failed to mark code as viewed "
                );

                updateBatchHistorySection(recoveryBatchSectionElement, resp.BATCH, resp.ITEM_PER_PAGE);
              
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
        
        messageContainerElement.classList.add("show");

        showTemporaryMessage(messageContainerElement, resp.MESSAGE);
        tableCoderSpinnerElement.style.display = "none";
        toggleSpinner(tableCoderSpinnerElement, false);

        setTimeout(() => {
              codeGenerationComplete();
         
        }, 5000)
      


    } else {
        const DEFAULT_MESSAGE = "Hang on we are trying to process your request.."
    
        showTemporaryMessage(messageContainerElement, DEFAULT_MESSAGE)
        tableCoderSpinnerElement.style.display = "none";
        toggleSpinner(tableCoderSpinnerElement, false);

        setTimeout(() => {
              codeGenerationComplete();
            messageContainerElement.classList.remove("show");
        }, 5000)
        return false;
    }

}


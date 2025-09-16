import appStateManager from "../state/appStateManager.js";
import { handleButtonAlertClickHelper, toggleProcessMessage } from "../helpers/handleButtonAlertClicker.js";
import { clearTestResultContainer, displayResults } from "./generateSetupElement.js";
import { handleFormSubmissionHelper } from "../helpers/formUtils.js";
import { toggleElement } from "../utils.js";
import fetchData from "../fetch.js";
import { getCsrfToken } from "../security/csrf.js";
import { doNothing } from "../utils.js";


const dynamicTestFormSetupElement = document.getElementById("dynamic-form-setup");
const testSetupFormElement        = document.getElementById("verify-setup-form");

const testSetupInputFieldElement  = document.getElementById("verify-code-input");

if (testSetupFormElement) {
    testSetupFormElement.addEventListener("submit", handleTestSetupFormSubmission);
    testSetupFormElement.addEventListener("input", handleTestSetupFormSubmission);
    testSetupFormElement.addEventListener("blur", handleTestSetupFormSubmission);
}



const VERIFY_SETUP_BUTTON  = "verify-code-btn";
const TEST_SETUP_LOADER    = "verify-setup-code-loader";

export default testSetupInputFieldElement;

let testVerifySpinnerElement;
let dynamicSetupButton;


export async function handleTestCodeVerificationSetupClick(e, verifySetupButtonID) {

    const formData = await handleTestSetupFormSubmission(e)

    if (!formData) return;

    const code = formData.verifyCode;

    const alertAttributes = {
        title: "Verify setup",
        text: `⚠️ Important: This application will now verify if your setup was correctly configured with the backend. 
                    This is a one time verification and will not be verified again on the next batch
                        Are you sure you want to continue?`,
        icon: "info",
        cancelMessage: "No worries! No action was taken",
        messageToDisplayOnSuccess: `
                    Great! Your codes are being verified, we let you know once it is ready.
                    You can continue using the app while we validate them.
                    We’ll notify you once they’re ready.
                    Please, don't close the page.
                `,
        confirmButtonText: "Yes, validate setup",
        denyButtonText: "No, don't validate setup"
    };

    const handleTestSetupFetchAPI = async () => {
        const data = await fetchData({
            url: "/auth/recovery-codes/verify-setup/",
            csrfToken: getCsrfToken(),
            method: "POST",
            body: { code: code },
            throwOnError: false,
        });

        return data;

    };

    const data = await handleButtonAlertClickHelper(e,
        verifySetupButtonID,
        testVerifySpinnerElement,
        alertAttributes,
        handleTestSetupFetchAPI,
    );


    if (data) {

        try {

            clearTestResultContainer();
            const isComplete = await displayResults(data);

            if (!data.FAILURE) {

                toggleElement(dynamicTestFormSetupElement);

                try {
                    // Removes the form after a successful test.
                    //
                    // The form is hidden via Jinja until the page refreshes, so it may not exist
                    // in the DOM yet. Attempting to remove it while hidden would raise an error.
                    toggleElement(testSetupFormElement);
                } catch (error) {
                    doNothing();
                }

            }
            testFormSectionElement.reset();

            if (isComplete) {
                appStateManager.setVerificationTest(false);
            }



        } catch (error) {
            doNothing();
            appStateManager.setVerificationTest(false);

        }
    }


}



export async function displayTestResults(data) {

    if (data) {

        try {

            clearTestResultContainer();
            const isComplete = await displayResults(data);

            if (!data.FAILURE) {

                toggleElement(dynamicTestFormSetupElement);

                try {
                    // Removes the form after a successful test.
                    //
                    // The form is hidden via Jinja until the page refreshes, so it may not exist
                    // in the DOM yet. Attempting to remove it while hidden would raise an error.
                    toggleElement(testSetupFormElement);
                } catch (error) {
                    doNothing();
                }

            }
            testFormSectionElement.reset();

            if (isComplete) {
                appStateManager.setVerificationTest(false);
            }

            toggleProcessMessage(false);


        } catch (error) {
            doNothing();
            toggleProcessMessage(false);

        }
    }

}





export function loadTestVerificationElements() { 
       
    if (!dynamicSetupButton) {
        dynamicSetupButton = document.getElementById(VERIFY_SETUP_BUTTON)
    }

    if (!testVerifySpinnerElement) {
        testVerifySpinnerElement =  document.getElementById(TEST_SETUP_LOADER);
    }

    
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
function handleTestSetupFormSubmission(e) {
    return handleFormSubmissionHelper(e, testSetupFormElement, ["verify_code"]);

}


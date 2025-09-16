import appStateManager from "./state/appStateManager.js";
import {toggleElement,} from "./utils.js";
import EnqueuedMessages from "./messages/enqueueMessages.js";
import { handleDeleteAllCodeButtonClick, handleDeleteCodeeButtonClick } from "./helpers/handleCodeDelete.js";
import { handleEmailCodeeButtonClick,  } from "./helpers/handleEmail.js";
import { handleGenerateCodeWithNoExpiryClick, handleIncludeExpiryDateCheckMark } from "./helpers/handleCodeGeneration.js";
import { handleTestCodeVerificationSetupClick } from "./codesSetupVerifcation/handleTestSetup.js";
import { handleRegenerateCodeButtonClick } from "./helpers/handleCodeGeneration.js";
import { handleInvalidateButtonClick } from "./helpers/handleInvalidation.js";
import { notify_user } from "./notify.js";
import { handleGenerateCodeWithExpiryClick } from "./helpers/handleCodeGeneration.js";
import { loadTestVerificationElements } from "./codesSetupVerifcation/handleTestSetup.js";
import { handleDownloadButtonClick } from "./helpers/handleDownload.js";
import invalidateFormElement from "./helpers/handleInvalidation.js";
import { handleInputFieldHelper } from "./helpers/handlers.js";
import { invalidateInputFieldElement } from "./helpers/handleInvalidation.js";
import { deleteInputFieldElement } from "./helpers/handleCodeDelete.js";
import testSetupInputFieldElement from "./codesSetupVerifcation/handleTestSetup.js";


// Elements
const recovryDashboardElement = document.getElementById("recovery-dashboard");
const navigationIconContainerElement = document.getElementById("navigation-icon-elements");



// event handlers


// input
invalidateInputFieldElement.addEventListener("input", handleInputFieldHelper);
deleteInputFieldElement.addEventListener("input", handleInputFieldHelper);

if (testSetupInputFieldElement) {
     testSetupInputFieldElement.addEventListener("input", handleInputFieldHelper);

}

// clicking

recovryDashboardElement.addEventListener("click", handleEventDelegation);


// invalidate code form elements


invalidateFormElement.addEventListener("click", handleInvalidateButtonClick);




// messages elements



// navigation icon
const hamburgerOpenIcon = document.getElementById("open-hamburger-nav-icon");
const closeXIcon = document.getElementById("close-nav-icon");


// Stats display board
const statsTotalCodesIssuedBoard = document.getElementById("stat__total_codes_issued")
const statsTotalCodesDownloadedBoard = document.getElementById("stat__total-codes-downloaded");
const statsTotalCodesEmailedBoard = document.getElementById("stat__total-codes-emailed");
const statsBatchCodesRemovedBoard = document.getElementById("stat__total-batch-codes-removed");
const statsCodesDeactivatedBoard = document.getElementById("stat__total-codes-deactivated");
const statsTotalCodesRemovedBoard = document.getElementById("stat__total-codes-removed")



// constants
const REGENERATE_BUTTON_ID = "regenerate-code-btn";
const DOWNLOAD_CODE_BTN_ID = "download-code-btn";
const GENERATE_CODE_WITH_EXPIRY_BUTTON_ID = "form-generate-code-btn";
const GENERATE_CODE_WITH_NO_EXPIRY = "generate-code-with-no-expiry-btn";
const CLOSE_NAV_BAR_ICON = "close-nav-icon";

const VERIFY_SETUP_BUTTON = "verify-code-btn";
const EMAIL_BUTTON_ID = "email-code-btn";
const DELETE_CURRENT_CODE_BUTTON_ID = "delete-current-code-btn";
const DELETE_ALL_CODES_BUTTON_ID = "delete-all-code-btn"
const OPEN_NAV_BAR_HAMBURGERR_ICON = "open-hamburger-nav-icon";
const EXCLUDE_EXPIRY_CHECKBOX_ID = "exclude_expiry"


const enqueuedMessages = new EnqueuedMessages();


document.addEventListener("DOMContentLoaded", () => {
    notify_user(enqueuedMessages.getEnqueuedMessages());

});


let alertMessage;



window.addEventListener("resize", handleResetDashboardState);





// Prevents the page from being refreshed or closed why a given action is being performed
window.addEventListener("beforeunload", function (event) {
    if (appStateManager.isCodeBeingGenerated() || appStateManager.isVerificationTestInProgress()) {
        event.preventDefault();
        event.returnValue = "";
        return "";
    }
});




function handleEventDelegation(e) {
    const buttonElement = e.target.closest("button");
    const inputElement = e.target.closest("input");
    const navigationIconElement = e.target.closest("i");


    if (buttonElement === null && inputElement === null && navigationIconElement === null) {
        return;
    }


    // Decide which element's ID to use:
    // Prefer buttonElement's id if it exists, otherwise use inputElement's id if exists, if not use the navigation elements id
    const elementID = buttonElement ? buttonElement.id : (inputElement ? inputElement.id : navigationIconElement.id);


    switch (elementID) {
        case GENERATE_CODE_WITH_EXPIRY_BUTTON_ID:
            appStateManager.setCodeGeneration(true)
            handleGenerateCodeWithExpiryClick(e, GENERATE_CODE_WITH_EXPIRY_BUTTON_ID);
            loadTestVerificationElements();
            appStateManager.setGenerateActionButtons(false);
            break;
        case GENERATE_CODE_WITH_NO_EXPIRY:
            appStateManager.setCodeGeneration(true)
            handleGenerateCodeWithNoExpiryClick(e, GENERATE_CODE_WITH_NO_EXPIRY);
            appStateManager.setGenerateActionButtons(false);
            loadTestVerificationElements();
            break;
        case EMAIL_BUTTON_ID:
            handleEmailCodeeButtonClick(e, EMAIL_BUTTON_ID);
            break;
        case EXCLUDE_EXPIRY_CHECKBOX_ID:
            handleIncludeExpiryDateCheckMark(e, EXCLUDE_EXPIRY_CHECKBOX_ID);
            break;
        case VERIFY_SETUP_BUTTON:
            appStateManager.setVerificationTest(true);
            handleTestCodeVerificationSetupClick(e, VERIFY_SETUP_BUTTON);
            break;
        case REGENERATE_BUTTON_ID:

            // alert message is only generated when the first code is generated
            // which means that it doesn't show up on initial load
            // However, after it shows up we don't want recall from DOM
            // if it already exists
            if (!alertMessage) {
                alertMessage = document.getElementById("alert-message");
            }

            appStateManager.setCodeGeneration(true)
            toggleElement(alertMessage);
            handleRegenerateCodeButtonClick(e, REGENERATE_BUTTON_ID, alertMessage);
            appStateManager.setRequestCodeRegeneration(true);
            break;

        case DELETE_CURRENT_CODE_BUTTON_ID:
            handleDeleteCodeeButtonClick(e, DELETE_CURRENT_CODE_BUTTON_ID)
            break;
        case DELETE_ALL_CODES_BUTTON_ID:
            handleDeleteAllCodeButtonClick(e, DELETE_ALL_CODES_BUTTON_ID, alertMessage)
            break;
        case DOWNLOAD_CODE_BTN_ID:
            handleDownloadButtonClick(e, DOWNLOAD_CODE_BTN_ID);
            break;
        case OPEN_NAV_BAR_HAMBURGERR_ICON:
            toggleSideBarIcon(navigationIconElement)
            break;

        case CLOSE_NAV_BAR_ICON:
            toggleSideBarIcon(navigationIconElement);
            break;

    }

}



/**
 * Resets certain dashboard elements to their default state on large screens (≥ 990px).
 */
function handleResetDashboardState() {
    const EXPECTED_WINDOW_WIDTH = 990;
    const currentWindowSize = window.innerWidth;

    hamburgerOpenIcon.style.display = "block";
    closeXIcon.style.display = "none";

    // Desktop view or greater
    if (currentWindowSize > EXPECTED_WINDOW_WIDTH) {
        recovryDashboardElement.style.paddingTop = "65px";
        recovryDashboardElement.style.marginTop = "0";
        navigationIconContainerElement.style.height = 0
        hamburgerOpenIcon.style.display = "none"

    }

}





function toggleSideBarIcon(navIconElement) {

    if (navIconElement.id !== OPEN_NAV_BAR_HAMBURGERR_ICON && navIconElement.id !== CLOSE_NAV_BAR_ICON) {
        return;
    }

    let isNavOpen = true;

    if (navIconElement.id === OPEN_NAV_BAR_HAMBURGERR_ICON) {
        navIconElement.classList.add("rotate-360")
    }

    if (navIconElement.id === CLOSE_NAV_BAR_ICON) {
        isNavOpen = false;
        navIconElement.classList.add("rotate-360");
    }

    setTimeout(() => {

        if (isNavOpen) {
            navIconElement.classList.remove("rotate-360");
            navIconElement.style.display = "none";
            closeXIcon.style.display = "block";

            navigationIconContainerElement.style.height = "auto";
            recovryDashboardElement.style.marginTop = "400px";

            navigationIconContainerElement.classList.add("active")

        } else {

            navIconElement.classList.remove("rotate-360");
            navIconElement.style.display = "none";
            closeXIcon.style.display = "none";
            hamburgerOpenIcon.style.display = "block";
            navigationIconContainerElement.style.height = "0";
            recovryDashboardElement.style.marginTop = "65px";
            navigationIconContainerElement.classList.remove("active")


        }


    }, 500);
}





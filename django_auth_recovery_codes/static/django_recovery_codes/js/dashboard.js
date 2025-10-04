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


// App state & utilities
import appStateManager from "./state/appStateManager.js";
import { toggleElement,checkIfHTMLElement } from "./utils.js";


// Code setup & test verification
import { handleTestCodeVerificationSetupClick, loadTestVerificationElements } from "./codesSetupVerifcation/handleTestSetup.js";
import testSetupInputFieldElement from "./codesSetupVerifcation/handleTestSetup.js";

// Helpers
import { handleDeleteAllCodeButtonClick, 
       handleDeleteCodeeButtonClick, 
       deleteInputFieldElement } from "./helpers/handleCodeDelete.js";
import { handleDownloadButtonClick } from "./helpers/handleDownload.js";
import { handleEmailCodeeButtonClick } from "./helpers/handleEmail.js";
import { handleGenerateCodeWithNoExpiryClick, 
         handleGenerateCodeWithExpiryClick, 
         handleIncludeExpiryDateCheckMark,
         handleRegenerateCodeButtonClick } from "./helpers/handleCodeGeneration.js";
import { handleInvalidateButtonClick } from "./helpers/handleInvalidation.js";
import invalidateFormElement, { invalidateInputFieldElement } from "./helpers/handleInvalidation.js";
import { handleInputFieldHelper } from "./helpers/handlers.js";
import { safeUIUpdate } from "./utils.js";

// Elements
const recovryDashboardElement        = document.getElementById("recovery-dashboard");
const navigationIconContainerElement = document.getElementById("navigation-icon-elements");


function oneTimeElementsCheck() {
    // === Dashboard & Navigation Containers ===
    checkIfHTMLElement(recovryDashboardElement,       "Recovery dashboard",         true);
    checkIfHTMLElement(navigationIconContainerElement,"Navigation icons container", true);
}


oneTimeElementsCheck();



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



// navigation icon
const hamburgerOpenIcon = document.getElementById("open-hamburger-nav-icon");
const closeXIcon = document.getElementById("close-nav-icon");


// constants
const REGENERATE_BUTTON_ID                = "regenerate-code-btn";
const DOWNLOAD_CODE_BTN_ID                = "download-code-btn";
const GENERATE_CODE_WITH_EXPIRY_BUTTON_ID = "form-generate-code-btn";
const GENERATE_CODE_WITH_NO_EXPIRY        = "generate-code-with-no-expiry-btn";
const CLOSE_NAV_BAR_ICON                  = "close-nav-icon";
const VERIFY_SETUP_BUTTON                 = "verify-code-btn";
const EMAIL_BUTTON_ID                     = "email-code-btn";
const DELETE_CURRENT_CODE_BUTTON_ID       = "delete-current-code-btn";
const DELETE_ALL_CODES_BUTTON_ID          = "delete-all-code-btn"
const OPEN_NAV_BAR_HAMBURGERR_ICON        = "open-hamburger-nav-icon";
const EXCLUDE_EXPIRY_CHECKBOX_ID          = "exclude_expiry"




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



/**
 * Handles event delegation for button, input, and navigation icon elements.
 * @param {Event} e - The click event object.
 * @returns 
 */
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
            appStateManager.setCodeGeneration(true);
            handleGenerateCodeWithExpiryClick(e, GENERATE_CODE_WITH_EXPIRY_BUTTON_ID);

            safeUIUpdate(() => {
                loadTestVerificationElements();
            })
          
            appStateManager.setGenerateActionButtons(true);
            break;
        case GENERATE_CODE_WITH_NO_EXPIRY:
            appStateManager.setCodeGeneration(true)
            handleGenerateCodeWithNoExpiryClick(e, GENERATE_CODE_WITH_NO_EXPIRY);
            appStateManager.setGenerateActionButtons(true);

             safeUIUpdate(() => {
                loadTestVerificationElements();
            })

            break;
        case EMAIL_BUTTON_ID:
            safeUIUpdate(() => {
                handleEmailCodeeButtonClick(e, EMAIL_BUTTON_ID);
            })
         
            break;
        case EXCLUDE_EXPIRY_CHECKBOX_ID:
            handleIncludeExpiryDateCheckMark(e);
            break;
        case VERIFY_SETUP_BUTTON:
            appStateManager.setVerificationTest(true);

            safeUIUpdate(async () => {
                await handleTestCodeVerificationSetupClick(e, VERIFY_SETUP_BUTTON);
            })
        
            break;
        case REGENERATE_BUTTON_ID:

            // alert message is only generated when the first code is generated
            // which means that it doesn't show up on initial load
            // However, after it shows up we don't want recall from DOM
            // if it already exists
            if (!alertMessage) {
                alertMessage = document.getElementById("alert-message");
            }

            appStateManager.setCodeGeneration(true);

            if (!appStateManager.isRequestCodeGenerationActive()) {
                appStateManager.setRequestCodeRegeneration(true);

            }
           
            toggleElement(alertMessage);
            
            safeUIUpdate(async () => {
                await handleRegenerateCodeButtonClick(e, REGENERATE_BUTTON_ID, alertMessage);
            });

          
           
            break;

        case DELETE_CURRENT_CODE_BUTTON_ID:
            safeUIUpdate(async () => {
                handleDeleteCodeeButtonClick(e, DELETE_CURRENT_CODE_BUTTON_ID)
            })
            break;
        case DELETE_ALL_CODES_BUTTON_ID:

            safeUIUpdate( async () => {
                 handleDeleteAllCodeButtonClick(e, DELETE_ALL_CODES_BUTTON_ID, alertMessage)
            })
           
            break;
        case DOWNLOAD_CODE_BTN_ID:

            safeUIUpdate(async () => {
                handleDownloadButtonClick(e, DOWNLOAD_CODE_BTN_ID);
            })
          
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




/**
 * Toggles the sidebar navigation icons and the sidebar state.
 *
 * This function handles the opening and closing animations of the navigation bar icons,
 * switches the display between the hamburger and close icons,
 *
 * @param {HTMLElement} navIconElement - The navigation icon element that was clicked.
 *                                        Must be either the open hamburger icon or the close icon.
 */
function toggleSideBarIcon(navIconElement) {

    const MILLI_SECONDS = 500;
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


    }, MILLI_SECONDS);
}




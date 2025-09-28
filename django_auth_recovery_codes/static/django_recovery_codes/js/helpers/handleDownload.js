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


import { showTemporaryMessage }                from "../messages/message.js";
import { toggleSpinner, toggleButtonDisabled } from "../utils.js";
import { updateButtonFromConfig }              from "../generateCodeActionButtons.js";
import messageContainerElement                 from "./appMessages.js";
import { handleButtonAlertClickHelper }        from "./handleButtonAlertClicker.js";
import fetchData                               from "../fetch.js";
import { getCsrfToken }                        from "../security/csrf.js";
import { buttonStates }                        from "../generateCodeActionButtons.js";
import { logError, warnError }                 from "../logger.js";
import { toggleProcessMessage }                from "./handleButtonAlertClicker.js";
import { markCurrentCardBatchAsDownload }      from "../batchCardsHistory/updateBatchHistorySection.js";
import { getOrFetchElement }                   from "../utils.js";

const DOWNLOAD_LOADER_ID               = "download-code-loader";
let   downloadCodeButtonElementSpinner = document.getElementById(DOWNLOAD_LOADER_ID); // Dynamic, doesn't exist at runtime



/**
 * Extracts the Content-Disposition header and filename from a Headers object.
 *
 * @param {Headers|Object} headers - The headers object from a fetch response.
 * @returns {Object} An object containing:
 *  - disposition {string|null} - The Content-Disposition header value, or null if not found.
 *  - filename {string|null} - The filename extracted from the header, or null if not present.
 */
function extractDispositionFromHeaders(headers) {

    if (typeof headers !== "object") {
        warnError("headers not found because headers is not a dictionary")
        return {disposition: null, filename: null}
    }
    return headers.get("Content-Disposition");

}


/**
 * Extracts the filename from a Content-Disposition header.
 *
 * @param {string|null} disposition - The Content-Disposition header value.
 * @returns {string} The extracted filename, or a default "downloaded_file" if not found.
 */
function getFilenameFromDisposition(disposition) {
    let filename = "downloaded_file";
   
    if (disposition && disposition.includes("filename=")) {
        filename = disposition.split("filename=")[1].replace(/['"]/g, "");
    }

    return filename;
}



/**
 * Triggers a file download from a fetch response.
 *
 * Extracts the filename from the Content-Disposition header and downloads
 * the file using a temporary <a> element. Also returns a success flag from headers.
 *
 * @param {Response} fetchResponse - The fetch Response object.
 * @returns {Promise<{success: boolean, filename: string}>} Object containing the success flag and downloaded filename.
 * @throws {Error} Throws if reading the response blob fails.
 */
async function triggerDownload(fetchResponse) {
  
    const disposition = extractDispositionFromHeaders(fetchResponse.headers);

    if (!disposition) {
        logError("extractDispositionFromHeaders", "Expected a disposition object but got null");
        return;
    }

    const filename = getFilenameFromDisposition(disposition);

    try {
        const blob        = await fetchResponse.blob();
        const url         = window.URL.createObjectURL(blob);
        const aElement    = document.createElement("a");
        aElement.href     = url;
        aElement.download = filename;
        aElement.click();
        aElement.remove();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        throw new Error(error.message)
    }

    const success  = fetchResponse.headers.get("X-Success") === "true";
    return { success, filename };
   
}



/**
 * Handles the UI updates after a successful recovery code download.
 *
 * - Hides the download spinner.
 * - Shows a temporary success message.
 * - Updates the download button state and re-enables it.
 * - Marks the current recovery code batch as downloaded.
 *
 * @param {Event} e - The click event from the download button.
 */
function handleDownloadSuccessMessageUI(e) {

    toggleSpinner(downloadCodeButtonElementSpinner, false)
    showTemporaryMessage(messageContainerElement, "Your recovery codes have successfully been downloaded");

    const btn = e.target.closest("button");
    toggleButtonDisabled(btn, false);
    updateButtonFromConfig(btn, buttonStates.downloaded, "You have already downloaded this code");
    toggleButtonDisabled(btn)

    markCurrentCardBatchAsDownload();

}


/**
 * Handles the UI updates when a recovery code download fails.
 *
 * - Logs a warning.
 * - Hides the download spinner.
 * - Shows a temporary failure message to the user.
 */
function handleDownloadFailureMessageUI() {
    
    warnError("handleDownloadButtonClick", "The button container element wasn't found");
    toggleSpinner(downloadCodeButtonElementSpinner, false)
    showTemporaryMessage(messageContainerElement, "Failed to download your recovery codes")

}



/**
 * Download a file from a Fetch Response object, with content-type validation.
 *
 * Also checks the `X-Success` header to determine if the server operation succeeded.
 * Throws an error if the response is HTML, preventing accidental download of error pages.
 *
 * @param {Response} resp - The Fetch Response object from the server.
 *
 * @returns {Promise<{success: boolean, filename: string}>} Resolves with an object containing:
 *   - success: boolean indicating whether the server reported success via `X-Success` header.
 *   - filename: the name of the downloaded file.
 *
 * @throws {Error} If the response Content-Type is HTML, indicating a potential error page.
 *
 * @example
 * const resp = await fetchData({ url: "/download-code/", returnRawResponse: true });
 * const { success, filename } = await downloadFromResponse(resp);
 * console.log("Download success:", success, "Filename:", filename);
 */
export async function downloadFromResponse(resp) {

    const contentType = resp.headers.get("Content-Type") || "";

    // Prevent downloading HTML pages which would likely result in error pages
    if (contentType.includes("text/html")) {
        const text = await resp.text();
        throw new Error(`Unexpected HTML response detected:\n${text}`);
    }


    return await triggerDownload(resp);
}


/**
 * Checks if a fetch response contains JSON and processes it.
 *
 * - Hides the download spinner.
 * - Attempts to parse the response as JSON.
 * - If successful, shows a temporary message from the JSON data.
 *
 * @param {Response} resp - The fetch Response object.
 * @returns {Promise<boolean>} Returns true if the response was JSON and processed successfully, otherwise false.
 */
async function ifJsonResponseAndProcess(resp) {
    toggleSpinner(downloadCodeButtonElementSpinner, false);

 
    const clone = resp.clone(); 

    try {
        const data = await clone.json();
        showTemporaryMessage(messageContainerElement, data.message || data.MESSAGE);
        return true;
    } catch {
        return false;
    }
}



/**
 * Handles the click event for the "Download code" button.
 * 
 * When clicked triggers a fetch API that allows the user to download
 * the recovery codes
 * 
 * @param {Event} e - The click event triggered by the button.
 */
export async function handleDownloadButtonClick(e, downloadButtonID) {

    const buttonElement = e.target;
    toggleButtonDisabled(buttonElement);
    const MILLI_SECONDS = 2000;

    toggleSpinner(downloadCodeButtonElementSpinner);

    showTemporaryMessage(messageContainerElement, "Preparing your download... just a moment!");
    

    const handleDownloadCodesApiRequest = async () => {

        const resp = await fetchData({
            url: "/auth/recovery-codes/download-codes/",
            csrfToken: getCsrfToken(),
            method: "POST",
            body: { forceUpdate: true },
            returnRawResponse: true,
        });

        return resp;

    }
    const resp = await handleButtonAlertClickHelper(e,
                                                    downloadButtonID,
                                                    {},
                                                    getOrFetchElement(downloadCodeButtonElementSpinner, DOWNLOAD_LOADER_ID),
                                                    handleDownloadCodesApiRequest,
                                                     )

    toggleProcessMessage(false);
    const isProcessed = await ifJsonResponseAndProcess(resp);
  
    if (isProcessed) {
        return;
    }

    const respData = await downloadFromResponse(resp);
   
    setTimeout(() => {
         toggleProcessMessage(false)
        if (respData && respData.success) {
            handleDownloadSuccessMessageUI(e);
            
            return;
        } 
        
        handleDownloadFailureMessageUI();
          
    }, MILLI_SECONDS)

}



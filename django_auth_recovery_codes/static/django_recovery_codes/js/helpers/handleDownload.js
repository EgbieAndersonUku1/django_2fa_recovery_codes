

import { showTemporaryMessage }                from "../messages/message.js";
import { toggleSpinner, toggleButtonDisabled } from "../utils.js";
import { updateButtonFromConfig }              from "../generateCodeActionButtons.js";
import messageContainerElement                 from "./appMessages.js";
import { messagePTag }                         from "./appMessages.js";
import { handleButtonAlertClickHelper }        from "./handleButtonAlertClicker.js";
import fetchData                               from "../fetch.js";
import { getCsrfToken }                        from "../security/csrf.js";
import { buttonStates }                        from "../generateCodeActionButtons.js";
import { logError, warnError }                 from "../logger.js";
import { toggleProcessMessage }                from "./handleButtonAlertClicker.js";



const downloadCodeButtonElementSpinner = document.getElementById("download-code-loader");


function extractDispositionFromHeaders(headers) {

    if (typeof headers !== "object") {
        warnError("headers not found because headers is not a dictionary")
        return {disposition: null, filename: null}
    }
    return headers.get("Content-Disposition");

}


function getFilenameFromDisposition(disposition) {
    let filename = "downloaded_file";
   
    if (disposition && disposition.includes("filename=")) {
        filename = disposition.split("filename=")[1].replace(/['"]/g, "");
    }

    return filename;
}

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




function handleDownloadSuccessMessageUI(e) {

    toggleSpinner(downloadCodeButtonElementSpinner, false)
    showTemporaryMessage(messageContainerElement, "Your recovery codes have successfully been downloaded");

    const btn = e.target.closest("button");
    toggleButtonDisabled(btn, false);
    updateButtonFromConfig(btn, buttonStates.downloaded, "You have already downloaded this code");
    toggleButtonDisabled(btn)

}

function handleDownloadFailureMessageUI(resp) {
    
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
                                                    downloadCodeButtonElementSpinner,
                                                    handleDownloadCodesApiRequest,
                                                     )

    toggleProcessMessage(false);
    const isProcessed = await ifJsonResponseAndProcess(resp);
  
    if (isProcessed) {
        return;
    }

    const respData = await downloadFromResponse(resp);
    // console.log(respData)
   
    setTimeout(() => {
         toggleProcessMessage(false)
        if (respData && respData.success) {
            handleDownloadSuccessMessageUI(e);
            return;
        } 
        
        handleDownloadFailureMessageUI();
          
    }, MILLI_SECONDS)

}

import { showTemporaryMessage } from "../messages/message.js";
import { toggleSpinner, toggleButtonDisabled } from "../utils.js";
import { updateButtonFromConfig } from "../generateCodeActionButtons.js";


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

    // Extract filename from headers
    const disposition = resp.headers.get("Content-Disposition");
    let filename      = "downloaded_file";

    if (disposition && disposition.includes("filename=")) {
        filename = disposition.split("filename=")[1].replace(/['"]/g, "");
    }

  
    const success = resp.headers.get("X-Success") === "true";

    // Convert response to Blob which would enable it to be downloaded
    const blob = await resp.blob();
    
    // Trigger download which shows up in the icon on the browser when item is downloading
    const url  = window.URL.createObjectURL(blob);
    const aElement    = document.createElement("a");
    aElement.href     = url;
    aElement.download = filename;
    aElement.click();
    aElement.remove();
    window.URL.revokeObjectURL(url);

    return { success, filename };
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
   
    toggleSpinner(downloadCodeButtonElementSpinner);
    messageContainerElement.classList.add("show");

    toggleButtonDisabled(buttonElement)

    messagePTag.textContent = "Preparing your download... just a moment!";

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

    const respData = await downloadFromResponse(resp)

    if (respData && respData.success) {

        toggleButtonDisabled(buttonElement, false);
        toggleSpinner(downloadCodeButtonElementSpinner, false)
        showTemporaryMessage(messageContainerElement, "Your recovery codes have successfully been downloaded");

        const btn = e.target.closest("button");
        updateButtonFromConfig(btn, buttonStates.downloaded, "You have already downloaded this code");
        toggleButtonDisabled(btn)


    } else {
        warnError("handleDownloadButtonClick", "The button container element wasn't found");

        toggleSpinner(downloadCodeButtonElementSpinner, false)
        showTemporaryMessage(messageContainerElement, "Failed to download your recovery codes")

    }

}
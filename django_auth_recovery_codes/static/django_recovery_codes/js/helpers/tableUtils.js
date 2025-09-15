import appStateManager from "../state/appStateManager.js";
import config from "../state/config.js";
import { generateCodeActionAButtons } from "../generateCodeActionButtons.js";
import { toggleSpinner, clearElement } from "../utils.js";


const codeActionContainerElement = document.getElementById("page-buttons");
const tableCoderSpinnerElement   = document.getElementById("table-loader");
const codeTableElement           = document.getElementById("table-code-view");

const messageContainerElement    = document.getElementById("messages");
const messagePTag                = document.getElementById("message-p-tag");

import { HTMLTableBuilder } from "../generateTable.js";

export function populateTableWithUserCodes(codes) {

    const tableObjectData = {
        classList: ["margin-top-lg"],
        id: "generated-codes-table",

    }

    const MILLI_SECONDS = 6000; // seconds is only for the message. It takes 5 seconds to make it journey up and down
    const colHeaders    = ["status", "codes"];

    const tableElement = HTMLTableBuilder(colHeaders, codes, tableObjectData);

    if (tableElement) {

        messageContainerElement.classList.add("show");
        messagePTag.textContent = "Your recovery codes are now ready...";

        setTimeout(() => {

            tableCoderSpinnerElement.style.display = "none"

            toggleSpinner(tableCoderSpinnerElement, false);
            pickRightDivAndPopulateTable(tableElement)
            messageContainerElement.classList.remove("show");

            appStateManager.setCodeGeneration(false)

            // show the code action buttons
            if (appStateManager.shouldGenerateCodeActionButtons) {
                showCodeActionsButton();
                return;
            }

            if (generaterecoveryBatchSectionElement === null) {
                clearElement(codeActionContainerElement);

            }

        }, MILLI_SECONDS)

    }

    return true;
}



function pickRightDivAndPopulateTable(tableCodesElement) {

    if (config.generateCodeActionButtons) {
       showCodeActionsButton();
       return;
    }

    if (codeTableElement) {
        clearElement(codeTableElement);
        codeTableElement.appendChild(tableCodesElement);
        return;
    }

    clearElement(tableCodeContainerDiv);
    tableCodeContainerDiv.appendChild(tableCodesElement);


}


function showCodeActionsButton() {
    const buttons = generateCodeActionAButtons();
    codeActionContainerElement.appendChild(buttons);
    appStateManager.setCodeGeneration(false);
    return;
}
  
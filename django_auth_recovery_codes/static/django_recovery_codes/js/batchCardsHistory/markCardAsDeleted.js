import { checkIfHTMLElement } from "../utils.js";
import { getCardFieldElements } from "./batchCardUtils.js";
import { markCardFieldHelper } from "./updateBatchHistorySection.js";


/**
 * Marks a card element as deleted by updating its status text and style.
 * Sets the status text to "Deleted", removes the "text-green" class, 
 * and adds "text-red" and "bold" classes to highlight the deletion.
 *
 * @param {HTMLElement|null} cardElement - The card element whose status should be updated.
 *                                         If null, the function does nothing.
 */
export function markCardAsDeleted(cardElement) {

    if (cardElement === null) return;

    checkIfHTMLElement(cardElement, "card element", true);

    const fieldElements = getCardFieldElements(cardElement);

    if (!fieldElements.length) return;

    markCardFieldHelper(cardElement,"status", "Deleted", "text-red");


}




import { checkIfHTMLElement } from "../utils.js";

/**
 * Get the field elements of a given card element.
 *
 * This function takes a card element and returns all field value
 * elements inside it (matched by `.card-head .info-box .value p`).
 * These elements represent fields such as `is_deleted`, `is_downloaded`,
 * `number_issued`, etc.
 *
 * @param {HTMLElement} cardElement - The card element to extract field values from.
 * @returns {NodeListOf<HTMLParagraphElement>} A list of field value elements.
 */
export function getCardFieldElements(cardElement) {
    
    checkIfHTMLElement(cardElement, "Card Element", true);

    const attributesElements = cardElement.querySelectorAll('.card-head .info-box .value p');
    return attributesElements;
}

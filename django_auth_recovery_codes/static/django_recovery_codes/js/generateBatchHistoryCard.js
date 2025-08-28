import { warnError } from "./logger.js";
import { formatIsoDate } from "./utils.js";


/**
 * Mapping of batch object keys to human-readable labels.
 *
 * This object is used to convert the internal field names of a recovery code batch
 * into user-friendly labels for display in the summary card.
 *
 * Keys correspond to the property names in a batch object, and values are
 * the labels that will appear in the HTML card.
 *
 * Example usage:
 * const label = batchKeysMapping.NUMBER_ISSUED; // "Number of Code issued"
 */

const batchKeysMapping = {
  ID: "ID",
  NUMBER_ISSUED: "Number of Code issued",
  NUMBER_REMOVED: "Number of removed",
  NUMBER_INVALIDATED: "Number of deactivated",
  NUMBER_USED: "Number of Code used",
  CREATED_AT: "Date issued",
  DOWNLOADED: "Has downloaded code batch",
  EMAILED: "Has emailed code batch",
  EXPIRY_DATE: "Expiry date",
  GENERATED: "Has generated code batch",
  MODIFIED_AT: "Date modified",
  STATUS: "Status",
  USERNAME: "User",
  VIEWED: "Has viewed code batch"
};



/**
 * Generates an HTML summary card for a batch of recovery codes.
 *
 * This function creates a <div> element representing a card that displays
 * summary information about the provided batch object. Each property
 * in the batch is converted into an info box within the card header.
 *
 * @param {Object} batch - An object representing a batch of recovery codes.
 *                         Keys correspond to batch fields, and values are the
 *                         associated data.
 *
 * @throws {Error} Throws an error if the input is not an object.
 *
 * @returns {HTMLElement} A <div> element representing the summary card, 
 *                        with child elements containing labelled info boxes 
 *                        for each field in the batch.
 *
 * @example
 * const batch = { id: 1, issued: 10, used: 2 };
 * const card = generateRecoveryCodesSummaryCard(batch);
 * document.body.appendChild(card);
 */
export function generateRecoveryCodesSummaryCard(batch) {

     if (typeof batch !== "object") {
        throw new Error(`The batch should be an array. Expected array but got an object with type ${typeof batch}`)
    }
  
    const cardElement     = document.createElement("div");
    const cardHeadElement = document.createElement("div");

    cardElement.className = "card";
    cardHeadElement.className = "card-head";

    for (let fieldName in batch) {
        let label = batchKeysMapping[fieldName];
        if (label === batchKeysMapping.ID) {
            label = label.toUpperCase()
    
        }
        const value = batch[fieldName];
        const infoBox = generateRecoveryCodesSummaryCardInfoBox(label, value, fieldName); // label, value, field  as the class name for card p info
        cardHeadElement.appendChild(infoBox)
    }

    cardElement.appendChild(cardHeadElement);
    return cardElement;
}



/**
 * Generates an individual info box element for a recovery codes summary card.
 *
 * This function creates a <div> element representing a single info box that displays
 * a label and its corresponding value from a batch object.
 *
 * @param {string} label - The human-readable label to display (from batchKeysMapping).
 * @param {*} value - The value corresponding to the label. Dates will be formatted
 *                    via `formatDateFieldIfApplicable`.
 * @param {string} fieldName - The key name of the field in the batch object. Used
 *                             for setting the CSS class on the value element.
 *
 * @returns {HTMLElement} A <div> element with class "info-box" containing two
 *                        child divs: "label" and "value", each with a <p> element
 *                        for text content.
 *
 * @example
 * const infoBox = generateRecoveryCodesSummaryCardInfoBox(
 *   "Number of Code issued",
 *   10,
 *   "NUMBER_ISSUED"
 * );
 * document.body.appendChild(infoBox);
 */
function generateRecoveryCodesSummaryCardInfoBox(label, value, fieldName) {

    const infoBoxElement = document.createElement("div");
    const labelElement   = document.createElement("div");
    const valueElement   = document.createElement("div");

    const pLabelElement  = document.createElement("p");
    const pValueElement   = document.createElement("p");

    infoBoxElement.className = "info-box";
    labelElement.className   = "label";
    valueElement.className   = "value";

    pLabelElement.textContent = label;
    pValueElement.textContent  = formatDateFieldIfApplicable(fieldName, value);

    if (fieldName) {
        fieldName = fieldName.toLowerCase();
    }

   
    pValueElement.className = fieldName;

    if (label === batchKeysMapping.STATUS  ){
        pValueElement.classList.add("text-green", "bold")
    }

  
    labelElement.appendChild(pLabelElement);
    valueElement.appendChild(pValueElement)


    infoBoxElement.appendChild(labelElement);
    infoBoxElement.appendChild(valueElement);

    return infoBoxElement;

}



/**
 * Conditionally formats a value if it belongs to a date field.
 * 
 * @param {string} fieldName - The class name or field key.
 * @param {string} value - The value to potentially format.
 * @returns {string} Formatted value if date, otherwise original value.
 */
function formatDateFieldIfApplicable(fieldName, value) {
  
  if (batchKeysMapping && typeof batchKeysMapping === "object") {

      const dateFields = [batchKeysMapping.CREATED_AT, batchKeysMapping.MODIFIED_AT];
      if (dateFields.includes(batchKeysMapping[fieldName])) {
        return formatIsoDate(value); 
    }

    return markCodeWithExpiryDateIfApplicableOrMarkAsDoesNotExpiry(fieldName, value)

   
  } else {
    warnError("formatDateFieldIfApplicatble", "Missing batch key recovery mapping object object")
  }

  return value;
}



/**
 * Conditionally formats a value if it belongs to a expiry date field.
 * However, if the field is null, marks it as doesn't expiry. Assumes
 * the file contains `batchKeyMapping` dictionary where the keys returned
 * from the backend are mapped into readable human format
 * 
 * @param {string} fieldName - The class name or field key.
 * @param {string} value - The value to potentially format.
 * @returns {string} Formatted value if date, otherwise marks it as doesn't expiry.
 */
function markCodeWithExpiryDateIfApplicableOrMarkAsDoesNotExpiry(fieldName, value) {
    const dateFields = [batchKeysMapping.EXPIRY_DATE];

    if (dateFields.includes(batchKeysMapping[fieldName])) {
        return value !== null ? formatIsoDate(value) : "Recovery code does not expiry"
    }

    return value
}


import { warnError } from "./logger.js";
import { formatIsoDate } from "./utils.js";


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





export function createRecordBatcbCard(batch) {

    if (typeof batch !== "object") {
        throw new Error(`The batch should be an array. Expected array but got an object with type ${typeof batch}`)
    }
    const divContainer          = document.createElement("div");
    const historyCardsContainer = document.createElement("div");
    const cards                 = document.createElement("div")
    divContainer.className      = "container";
    historyCardsContainer.className = "history-cards";
    cards.className                 = "cards"

    const batchElement = createCard(batch);
    historyCardsContainer.appendChild(batchElement);
    divContainer.appendChild(historyCardsContainer);
    return divContainer;

}


function createCard(batch) {
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
        const infoBox = createCardInfoBox(label, value, fieldName); // label, value, field  as the class name for card p info
        cardHeadElement.appendChild(infoBox)
    }

    cardElement.appendChild(cardHeadElement);
    return cardElement;
}


function createCardInfoBox(label, value, fieldName) {

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
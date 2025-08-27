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
    divContainer.appendChild(createH1Header())
    divContainer.appendChild(historyCardsContainer);
    return divContainer;

}


function createH1Header() {
    
    const fragment  = document.createDocumentFragment();
    const h1Element = document.createElement("h1");
    const hrElement = document.createElement("hr");

    h1Element.classList.add("margin-top-lg", "pb-sm", "medium-title")
    hrElement.classList.add("dividor", "margin-bottom-lg");

    h1Element.textContent = "Batch Details History";
    fragment.appendChild(h1Element);
    fragment.appendChild(hrElement);
    return fragment;


}

function createCard(batch) {
    const cardElement     = document.createElement("div");
    const cardHeadElement = document.createElement("div");

    cardElement.className = "card";
    cardHeadElement.className = "card-head";

    for (let key in batch) {
        let label = batchKeysMapping[key];
        if (label === batchKeysMapping.ID) {
            label = label.toUpperCase()
    
        }
        const value = batch[key];
        const infoBox = createCardInfoBox(label, value);
        cardHeadElement.appendChild(infoBox)
    }

    cardElement.appendChild(cardHeadElement);
    return cardElement;
}


function createCardInfoBox(label, value) {

    const infoBoxElement = document.createElement("div");
    const labelElement   = document.createElement("div");
    const valueElement   = document.createElement("div");

    const pLabelElement  = document.createElement("p");
    const pValueElement   = document.createElement("p");


    infoBoxElement.className = "info-box";
    labelElement.className   = "label";
    valueElement.className   = "value";

    pLabelElement.textContent = label;
    pValueElement.textContent  = value;

    labelElement.appendChild(pLabelElement);
    valueElement.appendChild(pValueElement)

    infoBoxElement.appendChild(labelElement);
    infoBoxElement.appendChild(valueElement);

    return infoBoxElement;

}
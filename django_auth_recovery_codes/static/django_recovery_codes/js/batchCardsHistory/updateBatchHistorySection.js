
import { toggleSpinner, getNthChildNested, checkIfHTMLElement, addChildWithPaginatorLimit } from "../utils.js";
import { generateRecoveryCodesSummaryCard } from "../generateBatchHistoryCard.js";
import { markCardAsDeleted } from "./markCardAsDeleted.js";



const dynamicBatchSpinnerElement = document.getElementById("dynamic-batch-loader");


export function incrementRecoveryCardField(cardBatchElement, fieldSelector, MILLI_SECONDS = 6000) {
    if (!checkIfHTMLElement(cardBatchElement)) {
        warnError(
            "incrementRecoveryCardField",
            `Expected a field p Element. Got object with type ${typeof cardBatchElement}`
        );
        return; 
    }

    const PElements = cardBatchElement.querySelectorAll('.card-head .info-box .value p');
    
    for (const pElement of PElements) {

        // Only increment fields with the correct class

        if (pElement.classList.contains(fieldSelector)) {
            const currentValue = parseInt(pElement.textContent || "0", 10);
            pElement.textContent = currentValue + 1;
        
            pElement.classList.add("text-green", "bold", "highlight");
            
            setTimeout(() => {
                pElement.classList.remove("highlight");
            }, MILLI_SECONDS);

            break;
        }
    }
}



export function updateCurrentRecoveryCodeBatchCard(sectionElement, fieldToUpdate, tagName="div", classSelector="card-head") {
    const currentCardBatch = getNthChildNested(sectionElement, 1, tagName, classSelector);

    switch(fieldToUpdate) {
        case "invalidate":
            incrementRecoveryCardField(currentCardBatch, "number_invalidated");
            break;
         case "delete":
            incrementRecoveryCardField(currentCardBatch, "number_removed");
            break;
        
    }
   
}


export function updateBatchHistorySection(sectionElement,
                                         batch, 
                                         batchPerPage = 5, 
                                         milliSeconds = 7000,
                                         tagName="div",
                                         classSelector="card-head",
                                         batchNumberToUpdate = 2,

                                        ) {
    const newBatchCard = generateRecoveryCodesSummaryCard(batch);
    
    let previousBatchCard;

    dynamicBatchSpinnerElement.style.display = "inline-block";
    toggleSpinner(dynamicBatchSpinnerElement);

    setTimeout(() => {
        addChildWithPaginatorLimit(sectionElement, newBatchCard, batchPerPage);

        previousBatchCard = getNthChildNested(
            sectionElement,
            batchNumberToUpdate,
            tagName,
            classSelector,
        );
        markCardAsDeleted(previousBatchCard);

        toggleSpinner(dynamicBatchSpinnerElement, false);
    }, milliSeconds);
}




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

import { toggleSpinner, 
       getNthChildNested, 
       checkIfHTMLElement, 
       addChildWithPaginatorLimit,
       getOrFetchElement, 
       toggleElement}                  from "../utils.js";
import { generateRecoveryCodesSummaryCard } from "../generateBatchHistoryCard.js";
import { markCardAsDeleted }                from "./markCardAsDeleted.js";
import { getCardFieldElements }             from "./batchCardUtils.js";
import { warnError }                        from "../logger.js";

import { recoveryBatchSectionElement }      from "./batchCardElements.js";


const DYNAMIC_BATCH_LOADER_ID    = "dynamic-batch-loader";
const allAcardsElements          = "#static-batch-cards-history .card";          
let dynamicBatchSpinnerElement   = document.getElementById(DYNAMIC_BATCH_LOADER_ID);


/**
 * Performs a one-time validation for static elements to ensure they exist in the DOM.
 * 
 * By validating elements once, we can safely use them in other functions without 
 * repeating `if` checks throughout the code.
 * 
 * Note: This is intended for static elements only. Dynamic elements 
 * (created or fetched at runtime) should be validated when they are used.
 */
function oneTimeElementsCheck() {
    checkIfHTMLElement(recoveryBatchSectionElement, "recovery batch section", true);
    checkIfHTMLElement(dynamicBatchSpinnerElement, "spinner element", true);
}


// run immediately
oneTimeElementsCheck();


/**
 * Returns the current card element by selecting the first nested
 * <div> with class "card-head" inside the recovery batch section.
 */
export function getCurrentCard() {
    const tagName       = "div";
    const classSelector = "card-head";
    return getNthChildNested(recoveryBatchSectionElement, 1, tagName, classSelector);
}


/**
 * Increments a numeric field within a recovery card UI element and highlights it temporarily.
 *
 * @param {HTMLElement} cardBatchElement - The container element of the recovery card.
 * @param {string} fieldSelector - The class name of the <p> element to increment.
 * @param {number} [MILLI_SECONDS=6000] - Duration in milliseconds to keep the highlight effect.
 */
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


/**
 * Increments the numeric value of a specific field inside a recovery card.
 * Highlights the updated field temporarily for visual feedback.
 *
 * @param {HTMLElement} cardBatchElement - The card batch container element.
 * @param {string} fieldSelector - The class name of the target <p> field to increment.
 * @param {number} [MILLI_SECONDS=6000] - Duration to keep the highlight before removal.
 */
export function updateCurrentRecoveryCodeBatchCard(fieldToUpdate) {
    const currentCardBatch = getCurrentCard();
   
    switch(fieldToUpdate) {
        case "invalidate":
            incrementRecoveryCardField(currentCardBatch, "number_invalidated");
            break;
         case "delete":
            incrementRecoveryCardField(currentCardBatch, "number_removed");
            break;
        case "used":
            incrementRecoveryCardField(currentCardBatch, "number_used");
            break;

        
    }
   
}




/**
 * Updates the batch history section with a new recovery codes card.
 * Adds the new card, marks the specified previous card as deleted,
 *
 * Also ensures the number of cards displayed respects the pagination
 * limit set by the backend. For example, if the limit is 5 cards per
 * page, the function prevents more than 5 cards from appearing on a
 * single page, automatically spilling excess into a new page. 
 * 
 * Using the scenerio above 7 cards will be displayed as following
 * 
 * Page 1 = 5 cards
 * Page 2 = 2 cards
 * 
 *  
 * @param {HTMLElement} sectionElement - Container for batch cards.
 * @param {Object} batch - Data used to generate the new recovery codes card.
 * @param {number} [batchPerPage=5] - Maximum number of cards allowed in the section.
 * @param {number} [milliSeconds=7000] - Delay before applying updates.
 * @param {string} [tagName="div"] - Tag name used for locating the card.
 * @param {string} [classSelector="card-head"] - Class selector for locating the card.
 * @param {number} [batchNumberToUpdate=2] - Index of the previous batch card to mark as deleted.
 */
export function updateBatchHistorySection(sectionElement,
                                         batch, 
                                         batchPerPage = 5, 
                                         milliSeconds = 7000,
                                         tagName="div",
                                         classSelector="card-head",
                                         batchNumberToUpdate = 3,

                                        ) {

                   
    const newBatchCard = generateRecoveryCodesSummaryCard(batch);
    
    let previousBatchCard;
    
    dynamicBatchSpinnerElement  = getOrFetchElement(dynamicBatchSpinnerElement, DYNAMIC_BATCH_LOADER_ID);
    if (dynamicBatchSpinnerElement) {
           dynamicBatchSpinnerElement.style.display = "inline-block";
            toggleSpinner(dynamicBatchSpinnerElement);
    }
 
    addChildWithPaginatorLimit(sectionElement, newBatchCard, batchPerPage);

    toggleElement(sectionElement, false);
    setTimeout(() => {
       
        previousBatchCard = getNthChildNested(
            sectionElement,
            batchNumberToUpdate,
            tagName,
            classSelector,
        );
        
        //  markCardAsDeleted(previousBatchCard)
        markOnlyTopCardAsActive();
        toggleSpinner(dynamicBatchSpinnerElement, false);
    }, milliSeconds);
}



/**
 * Updates a field in the current card by class name.
 * Sets its text content to the given value and applies a highlight class.
 *
 * @param {string} className - Target field’s class name.
 * @param {string} value - New value to assign to the field.
 * @param {string} [classColourSelector="text-green"] - CSS class applied for styling.
 */
export function markCardFieldHelper(cardEement, className, value, classColourSelector = "text-green") {
    
    const fieldElements = getCardFieldElements(cardEement);
    if (!fieldElements) return

    if (!fieldElements.length) return;

    for (const pElement of fieldElements) {
        if (pElement.classList.contains(className)) {
            pElement.textContent = value;
            pElement.classList.add(classColourSelector);
            break;
        }
    }
}




/**
 * Marks only the top card as active.
 *
 * This function selects all card elements that are visible in the DOM/UI
 *  and  marks all cards as deleted but then marks the current (top) card as active.
 *
 * Dependencies:
 * - markCardAsDeleted(cardElement): marks a given card as deleted.
 * - markCurrentCardAsActive(): marks the current card as active.
 */
function markOnlyTopCardAsActive() {
    const cardsElement = Array.from(document.querySelectorAll(allAcardsElements));
    
    if (cardsElement.length === 0) return;

    cardsElement.forEach((cardElement) => markCardAsDeleted(cardElement));
    markCurrentCardAsActive();
}


/**
 * Marks the current card batch as downloaded.
 */
export function markCurrentCardBatchAsDownload() {
    markCardFieldHelper(getCurrentCard(), "downloaded", "True");
}


/**
 * Marks the current card batch as emailed.
 */
export function markCurrentCardBatchAsEmailed() {
    markCardFieldHelper(getCurrentCard(), "emailed", "True");
}


/**
 * Marks the current card batch as Active
 */
export function markCurrentCardAsActive() {
    markCardFieldHelper(getCurrentCard(), "status", "Active");
}


/**
 * Marks the current card batch as viewed
 */
export function markCurrentCardBatchAsViewed() {
    markCardFieldHelper(getCurrentCard(), "viewed", "True")
}
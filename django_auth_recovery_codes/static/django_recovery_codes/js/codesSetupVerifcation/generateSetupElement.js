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


import { toggleSpinner, checkIfHTMLElement } from "../utils.js";

const resultContainer = document.getElementById("dynamic-verify-form-container");

const MILLI_SECONDS = 1000;

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
    checkIfHTMLElement(resultContainer, "result container", true);
}


// run right away
oneTimeElementsCheck();


/**
 * Clears all content from the test result container.
 */
export function clearTestResultContainer() {
    resultContainer.innerHTML = "";
}



/**
 * Displays test results received inside the result container with a title and
 * individual result messages. Results are shown sequentially with
 * a delay between each for better readability. Success messages
 * appear in green and failure messages in red.
 *
 * @param {Object} results - Key-value pairs of test outcomes.
 */
export async function displayResults(results) {
    const divTestResultContainer     = document.createElement("div");
    const MILLI_SECONDS              = 1000;
    divTestResultContainer.id        = "test-result"
    divTestResultContainer.className = "padding-top-md";

    divTestResultContainer.classList.add("margin-top-lg");
    
    const titleElement = createTitle();
    resultContainer.appendChild(titleElement);

    const keys = Object.keys(results).filter(key => key !== "SUCCESS");

    keys.forEach((key, index) => {

        setTimeout(() => {
            const message = results[key];

            if (key !== "FAILURE") {

                if (message) {
            
                    const divResult = createResultDiv(message);
                    divResult.classList.remove("text-red", "text-green")
                
                    results.FAILURE ? divResult.classList.add("text-red") : divResult.classList.add("text-green")
            
                    resultContainer.appendChild(divResult);
                }
            }
            
          
        }, index * MILLI_SECONDS); 

     return true 
    });
}


/**
 * Creates a title element for the test results.
 *
 * @param {string} [title="Test setup result"] - Text content of the title.
 * @param {string} [className="bold"] - CSS class applied to the title.
 * @returns {HTMLElement} The created title element.
 */
function createTitle(title = "Test setup result",  className = "bold") {
    return createResultDiv(title, className);
}


/**
 * Creates a styled result div containing a spinner and a message.
 * The spinner is shown initially and removed after a delay, 
 * while the message is appended to the result container.
 *
 * @param {string} message - Text content of the result message.
 * @param {string|null} [className=null] - Optional CSS class to style the message.
 * @returns {HTMLElement} The constructed result container element.
 */
function createResultDiv(message, className = null) {

    const divContainer = document.createElement("div");
    const divSpinner   = document.createElement("div");
    const divResult    = document.createElement("div");
    const spanElement  = document.createElement("span");
    const pElement     = document.createElement("p");

    divContainer.classList.add("result-div", "two-column-grid--5-95");
    divSpinner.classList.add("spinner");


    spanElement.classList.add("loader", "bg-green", "test-loader");
    divResult.classList.add("result-title");

    const icon     = document.createElement("i");
    icon.className = "fa-brands fa-hashnode";

    pElement.appendChild(icon);
    pElement.appendChild(document.createTextNode(` ${message}`));

    if (className !== null) {
        pElement.className = className;
    }

    toggleSpinner(spanElement)

    divSpinner.appendChild(spanElement);
    divContainer.appendChild(divSpinner);
   
    setTimeout(() => {

        divContainer.appendChild(divResult);
      
    }, MILLI_SECONDS * 2)

     setTimeout(() => {
        divResult.appendChild(pElement);
        toggleSpinner(spanElement, false);
    }, MILLI_SECONDS * 3)
   
  
    return divContainer;

}



import { specialChars } from "./specialChars.js";

/**
 * Shows the spinner for a specified duration and then hides it.
 * 
 * This function uses the `toggleSpinner` function to show the spinner immediately,
 * and then hides it after the specified amount of time (default is 500ms).
 * 
 * @param {HTMLElement} spinnerElement - The spinner element to display.
 * @param {number} [timeToDisplay=500] - The duration (in milliseconds) to display the spinner. Defaults to 500ms.
 */
export function showSpinnerFor(spinnerElement, timeToDisplay = 500, hideToggle=false) {
    toggleSpinner(spinnerElement); 

    setTimeout(() => {
        toggleSpinner(spinnerElement, false, hideToggle);  
    }, timeToDisplay);
}



/**
 * Toggles the visibility of the spinner.
 * 
 * This function shows or hides the spinner by setting its display property to either 'block' or 'none'.
 * 
 * @param {boolean} [show=true] - A boolean indicating whether to show or hide the spinner.
 *                               If `true`, the spinner is shown; if `false`, it is hidden.
 */
export function toggleSpinner(spinnerElement, show=true) {
   
    if (!checkIfHTMLElement(spinnerElement)) {
        return;
    };

    if (show) {
        spinnerElement.classList.add("show-spinner");
        return;
    }

    spinnerElement.classList.remove("show-spinner");

   
}


export function checkIfHTMLElement(element, elementName = "Unknown") {
    if (!(element instanceof HTMLElement || element instanceof DocumentFragment)) {
        console.error(`Could not find the element: '${elementName}'. Ensure the selector is correct.`);
        return false;
    }
    return true;
}





/**
 * Formats input text by inserting a dash ('-') at specified intervals.
 * 
 * This function listens for input changes and automatically adds dashes 
 * after every specified number of characters. It also provides an option
 * to keep only digits by removing all non-numeric characters.
 * 
 * @param {Event} e - The input event containing the target value.
 * @param {number} lengthPerDash - The number of characters between dashes (default: 5).
 * @param {boolean} digitsOnly - If true, removes all non-numeric characters (default: false).
 */
export function applyDashToInput(e, lengthPerDash=5, digitsOnly=false) {
  
    const value = e.target.value.trim();
  
    if (!value) return;
    if (!Number.isInteger(lengthPerDash)) {
        console.error(`The lengthPerDash must be integer. Expected an integer but got ${typeof lengthPerDash}`);
    };

    let santizeValue   = sanitizeText(value, digitsOnly);
    let formattedText  = [];


    for (let i=0; i < santizeValue.length; i++) {

        const fieldValue = santizeValue[i];
    
        if (i > 0 && i % lengthPerDash === 0 ) {
            formattedText.push(concatenateWithDelimiter("-", fieldValue));
        } else {
            formattedText.push(fieldValue);
            
        }
    }

   e.target.value = formattedText.join("");
   
};


/**
 * Concatenates two strings with a delimiter in between.
 * @param {string} first     - The first string.
 * @param {string} second    - The second string.
 * @param {string} delimiter - The delimiter to use if none is provide concatenates the two strings.
 * @returns {string}         - The concatenated string.
 */
export function concatenateWithDelimiter(first, second, delimiter = "") {
    return `${first}${delimiter}${second}`;
}



/**
 * Sanitizes the input text based on the specified criteria:
 * - Optionally removes non-numeric characters.
 * - Optionally removes non-alphabet characters.
 * - Optionally ensures that specific special characters are included and valid.
 * - Removes hyphens from the input text.
 * 
 * Note:
 * - To use this function, import `specialChars` from `specialChar.js`
 *   or define your own. If you define your own make sure to call it `specialChars`
 *   so the function doesn't throw an error, since it expects that name.
 * 
 * - Using an object (dictionary) for `specialChars` is recommended over an array
 *   for O(1) lookups instead of O(n) with `.includes()`.
 *
 * 
 * @param {string} text - The input text to be sanitized.
 * @param {boolean} [onlyNumbers=false] - If true, removes all non-numeric characters.
 * @param {boolean} [onlyChars=false] - If true, removes all non-alphabetic characters.
 * @param {Array<string>} [includeChars=[]] - An array of special characters that should be included in the text.
 * @throws {Error} If `includeChars` is not an array or contains invalid characters that are not in the `specialChars` list.
 * @returns {string} - The sanitized version of the input text.
 *
 * @example
 * // Only numbers will remain (non-numeric characters removed)
 * sanitizeText('abc123', true); 
 * // Output: '123'
 *
 * @example
 * // Only alphabetic characters will remain (non-alphabet characters removed)
 * sanitizeText('abc123!@#', false, true);
 * // Output: 'abc'
 *
 * @example
 * // Ensures specific special characters are valid (will remove invalid ones)
 * sanitizeText('@hello!world', false, false, ['!', '@']);
 * // Output: '@hello!world' (if both '!' and '@' are in the valid list of special characters)
 *
 * @example
 * // Removes hyphens from the input
 * sanitizeText('my-name-is', false, false);
 * // Output: 'mynameis'
 */
export function sanitizeText(text, onlyNumbers = false, onlyChars = false, includeChars = []) {
    if (!Array.isArray(includeChars)) {
        throw new Error(`Expected an array but got type ${typeof includeChars}`);
    }

    const INCLUDE_CHARS_ARRAY_LENGTH = includeChars.length;

    if (!Array.isArray(includeChars)) {
        throw new Error(`Expected an array but got ${typeof includeChars}`);
    }

    // Helper to check if a the special char is valid since the user can
    // define or import their own list
    const isValidSpecialChar = (char) => {
        if (Array.isArray(specialChars)) {
            return specialChars.includes(char); // O(n)
        }
        if (typeof specialChars === 'object' && specialChars !== null) {
            return Boolean(specialChars[char]); // O(1)
        }
        throw new Error('specialChars must be an array or object.');
    };

    if (INCLUDE_CHARS_ARRAY_LENGTH > 0) {
        const invalidChar = includeChars.find(char => !isValidSpecialChar(char));
        if (invalidChar) {
            throw new Error(`Expected a special character but got ${invalidChar}. Check if the special character js file is also imported`);
        }
    }

    if (onlyNumbers) {
        return text.replace(/\D+/g, ""); 
    }

    if (onlyChars) {
        if (INCLUDE_CHARS_ARRAY_LENGTH > 0) {
            return text.replace(/[^A-Za-z]/g, (match) => {
                return includeChars.includes(match) ? match : '';  // Keep if allowed, otherwise remove
            });
        }
     
        return text.replace(/[^A-Za-z]/g, '');
    }

    return text ? text.split("-").join("") : ''; 
}


export function toggleButtonDisabled(buttonElement, disable = true) {
    if (!buttonElement || buttonElement.tagName !== "BUTTON") return; 
    
    buttonElement.disabled = disable;
    
}



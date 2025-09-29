
import { logError, warnError } from "./logger.js";
import { specialChars }        from "./specialChars.js";


/**
 * Shows the spinner for a specified duration and then hides it.
 * 
 * This function uses the `toggleSpinner` function to show the spinner immediately,
 * and then hides it after the specified amount of time (default is 500ms).
 * 
 * @param {HTMLElement} spinnerElement - The spinner element to display.
 * @param {number} [timeToDisplay=500] - The duration (in milliseconds) to display the spinner. Defaults to 500ms.
 */
export function showSpinnerFor(spinnerElement, timeToDisplay = 500) {
    
    toggleSpinner(spinnerElement); 
    spinnerElement.style.display = "inline-block";
    setTimeout(() => {
        spinnerElement.style.display = "none";
        toggleSpinner(spinnerElement, false);  
    }, timeToDisplay);
}



/**
 * Toggles the visibility of a spinner element.
 *
 * This function shows or hides the spinner by adding or removing the
 * "show-spinner" class and, if necessary, setting its `display` style
 * to 'none' to ensure it is hidden.
 *
 * @param {HTMLElement} spinnerElement - The spinner element to toggle.
 * @param {boolean} [show=true] - Whether to show or hide the spinner.
 *                                `true` shows the spinner, `false` hides it.
 * @param {boolean} [silent=true] - If `false`, logs a message when the
 *                                  element is not found. If `true`, suppresses messages.
 */
export function toggleSpinner(spinnerElement, show = true, silent = true) {
    if (!checkIfHTMLElement(spinnerElement, "spinner element", silent)) {
        return false;
    }

    if (show) {
        spinnerElement.classList.add("show-spinner");
        return;
    }

    spinnerElement.classList.remove("show-spinner");
    spinnerElement.style.display = "none"; // force hide in case class removal doesn’t work
}



/**
 * Converts an ISO 8601 date string into a human-readable, localized format.
 * 
 * By default, formats dates in British English (en-GB) with 12-hour time
 * and lowercase a.m./p.m., e.g., "Aug. 27, 2025, 4:25 p.m.".
 * 
 * @param {string} isoDate - The ISO 8601 date string to format, e.g., "2025-08-27T16:25:06.535Z".
 * @param {string} [locale="en-GB"] - Optional locale code for formatting, e.g., "en-US" or "en-GB".
 * @returns {string} A formatted, human-readable date string.
 *
 * @example
 * formatIsoDate("2025-08-27T16:25:06.535Z");
 * // Returns: "Aug. 27, 2025, 4:25 p.m."
 * 
 * @example
 * formatIsoDate("2025-08-27T16:25:06.535Z", "en-US");
 * // Returns: "Aug. 27, 2025, 4:25 p.m."
 */
export function formatIsoDate(isoDate, locale = "en-GB") {
  const date = new Date(isoDate);

  const formatted = date.toLocaleString(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true
  })
  .replace("AM", "a.m.").replace("PM", "p.m.")
  .replace(/(\w+)\s/, "$1. ");

  return formatted;
}


export function checkIfHTMLElement(element, elementName = "Unknown", silent = false) {
    const msg = `Could not find the element: '${elementName}'. Ensure the selector is correct.`;
    return checkIfCorrectHTMLElementHelper(element, HTMLElement, msg, silent);

}


export function checkIfFormHTMLElement(formElement, silent = false) {
    const msg = `The element entered is not a form element. Expected a form element got ${typeof formElement}`;
    return checkIfCorrectHTMLElementHelper(formElement, HTMLFormElement, msg, silent)  
    
}


export function checkIfInputHTMLElement(inputElement, silent) {
    const msg = `The element entered is not a form element. Expected a form element got ${typeof inputElement}`;
    return checkIfCorrectHTMLElementHelper(inputElement, HTMLInputElement, msg, silent);
  
}


/**
 * Checks whether an element is an instance of a specified HTML element type.
 *
 * @param {any} element - The element to check.
 * @param {Function} htmlElement - The expected constructor, e.g., HTMLElement, HTMLDivElement.
 * @param {string} msg - Message to log or throw if the check fails.
 * @param {boolean} [throwError=false] - Whether to throw an error if the check fails.
 * @param {boolean} [silent=false] - If true, suppresses console warnings.
 * @returns {boolean} True if the element is of the expected type, false otherwise.
 */
function checkIfCorrectHTMLElementHelper(element, htmlElement, msg, throwError = false, silent = false) {
    if (!(element instanceof htmlElement)) {
        if (!silent) {
            warnError("checkIfCorrectHTMLElementHelper", msg);
            return false;
        }
        if (throwError) {
            throw new Error(msg);
        }
        return false;
    }
    return true;
}


/**
 * Performs a one-time validation for static elements to ensure they exist in the DOM.
 * 
 * By validating elements once, we can safely use them in other functions without 
 * repeating `if` checks throughout the code.
 * 
 * Note: This function is intended for static elements only. Dynamic elements 
 * (created or fetched at runtime) should be validated when they are used.
 */



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
        const msg = `The lengthPerDash must be integer. Expected an integer but got ${typeof lengthPerDash}`;
        warnError("applyDashToInput", msg);
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




/**
 * Enables or disables a button element.
 *
 * @param {HTMLButtonElement} buttonElement - The button element to enable or disable.
 * @param {boolean} [disable=true] - Whether to disable the button (true) or enable it (false).
 *
 * Notes:
 * - If the provided element is null, undefined, or not a <button>, the function does nothing.
 * - This is a simple utility for toggling button interactivity.
 */
export function toggleButtonDisabled(buttonElement, disable = true) {
    if (!buttonElement || buttonElement.tagName !== "BUTTON") return; 
    
    buttonElement.disabled = disable;
}



/**
 * Converts a string to title case (capitalises the first character and lowercases the rest).
 *
 * @param {string} text - The string to convert.
 * @returns {string} The converted string with the first character capitalised.
 *
 * @throws {Error} If the provided value is not a string.
 *
 * Example:
 *   toTitle("hello")    // returns "Hello"
 *   toTitle("WORLD")    // returns "World"
 */
export function toTitle(text) {
    if (typeof text != "string") {
        throw new Error(`Expected a string but got text with type ${text} `);
    }

    const title = `${text.charAt(0).toUpperCase()}${text.slice(1).toLowerCase()}`;
    return title;
}




/**
 * Pauses execution for a specified duration.
 *
 * @param {number} ms - The duration to sleep in milliseconds.
 * @returns {Promise<void>} A promise that resolves after the specified time.
 *
 * Example usage:
 *   await sleep(1000); // pauses execution for 1 second
 *
 * Notes:
 * - This function is useful in async functions to create delays without blocking the main thread.
 */
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}



/**
 * Prepends a new child element to a parent element.
 *
 * @param {HTMLElement} parent - The parent element to which the new child will be added.
 * @param {HTMLElement} newChild - The element to prepend to the parent.
 *
 * Notes:
 * - Uses the modern `prepend()` method if available.
 * - Falls back to `insertBefore()` for older browsers that do not support `prepend()`.
 * - Ensures the new child is added as the first child of the parent element.
 *
 * Example usage:
 *   const parent = document.getElementById("container");
 *   const newDiv = document.createElement("div");
 *   prependChild(parent, newDiv);
 */
export function prependChild(parent, newChild) {

  
  if (typeof parent.prepend === "function") {
    // Modern browsers
    parent.prepend(newChild);
   
  } else {
    // Fallback for older browsers (like IE)
    parent.insertBefore(newChild, parent.firstChild || null);
   
  }
}



/**
 * Returns the nth child element of a given parent, optionally filtered by tag name.
 *
 * @param {HTMLElement} parent - The parent HTML element.
 * @param {number} n - The 1-based index of the child (1 = first child).
 * @param {string} [tagName] - Optional tag name to filter by (e.g., 'div', 'span').
 * @returns {HTMLElement|null} The nth matching child or null if not found.
 */
export function getNthChildFast(parent, n, tagName) {
  if (!checkIfHTMLElement(parent, "getNthChildFast")) return null;

  if (typeof n !== "number" || !Number.isInteger(n) || n < 1) {
    logError("getNthChildFast", `The value 'n' must be a positive integer. Got: ${n}`);
    return null;
  }

  let children = Array.from(parent.children);

  if (tagName) {
    children = children.filter(child => child.tagName.toLowerCase() === tagName.toLowerCase());
  }

  return children[n - 1] || null; // 1-based index
}


/**
 * Returns the nth child of a parent element, optionally filtering by tag name,
 * and optionally returning a nested child by class name. This is useful 
 * because it doesn't query the DOM to find a nested element, making it more
 * efficient for dynamic dashboards.
 *
 * @param {HTMLElement} parent - The parent element.
 * @param {number} n - 1-based index of the child (1 = first child).
 * @param {string} [tagName] - Optional tag name to filter by (e.g., "div").
 * @param {string} [nestedClass] - Optional class name to get a nested child of the nth child.
 * @returns {HTMLElement|null} The element found or null if not found.
 */
export function getNthChildNested(parent, n, tagName, nestedClass) {
    
  const nthChild = getNthChildFast(parent, n, tagName);

  if (!nthChild) return null;

  if (nestedClass) {
    // Find the first direct child with the specified class
    return Array.from(nthChild.children).find(c => c.classList.contains(nestedClass)) || null;
  }

  return nthChild;
}



/**
 * Safely removes the last child element from a given parent container.
0 * 
 * This function checks whether the parent element has any children
 * and only removes the last child if it exists. It does not throw
 * an error if the container is empty.
 *
 * @param {HTMLElement} parentElement - The parent container whose last child will be removed.
 */
export function removeLastChild(parentElement) {
    if (parentElement.lastElementChild) {
        parentElement.removeChild(parentElement.lastElementChild);
    }
}


/**
 * Checks if the number of children in the parent exceeds the given page limit.
 *
 * @param {HTMLElement} parentElement - The container to check.
 * @param {number} pageLimit - The maximum number of children allowed.
 * @returns {boolean} True if the child count exceeds the limit, false otherwise.
 */
export function exceedsPaginatorLimit(parentElement, pageLimit) {
  
    if (!Number.isInteger(pageLimit)) {
        logError(
            "exceedsPaginatorLimit",
            `The page limit must be an integer. Got: ${pageLimit} (${typeof pageLimit})`
        );
        return false;
    }
    return parentElement.children.length >= pageLimit;
}



/**
 * Adds a new child element to a parent container while enforcing a maximum 
 * number of children (paginator limit). If the number of children exceeds 
 * the specified page limit, the last child elements are removed until the 
 * count is valid before adding the new element.
 *
 * @param {HTMLElement} parentElement - The container to which the new element will be added.
 * @param {HTMLElement} elementToAdd - The element to append or prepend to the parent container.
 * @param {number} pageLimit - The maximum number of children allowed in the parent container.
 * @param {boolean} [appendToTop=false] - If `true`, the element is appended to the bottom of the container; 
 *                                        if `false`, it is prepended to the top.
 *
 * @description
 * This function ensures that adding new elements to a container never exceeds the 
 * parent’s paginator limit. It performs the following checks:
 *   - Validates that `parentElement` and `elementToAdd` are valid HTML elements.
 *   - Validates that `appendToTop` is a boolean.
 *   - Removes the last child elements if the container exceeds the `pageLimit`.
 *   - Adds the new element to the top or bottom of the container depending on `appendToTop`.
 *
 * This is particularly useful for dynamically updating UI sections such as 
 * recovery code batch summaries while ensuring the pagination rules are enforced.
 */
export function addChildWithPaginatorLimit(parentElement, elementToAdd, pageLimit, appendToTop = false) {

    if (!checkIfHTMLElement(parentElement) && !checkIfHTMLElement(elementToAdd) ) {
        warnError("addChildWithPaginatorLimit", "The parentElement or elementToAdd is not a valid HTML");
        return;

    }
    
    if (typeof appendToTop !== "boolean") {
        warnError("addChildWithPaginatorLimit", `The appendToTop variable must be a boolean, expected a boolean object but got ${appendToTop} `);
        return;
    }

    while (exceedsPaginatorLimit(parentElement, pageLimit)) {
        removeLastChild(parentElement);
    }

    if (appendToTop) {
        parentElement.appendChild(elementToAdd)
    } else {
        prependChild(parentElement, elementToAdd)
    }


}




/**
 * Shows or hides a DOM element by toggling the "d-none" CSS class.
 *
 * @param {HTMLElement} element - The element to show or hide.
 * @param {boolean} [hide=true] - If true, hides the element; if false, shows it.
 *
 * Notes:
 * - If the element is null, undefined, or not provided, the function logs a message and does nothing.
 * - Uses the "d-none" class to control visibility, which should be defined in your CSS.
 *
 * Example usage:
 *   toggleElement(myDiv);        // hides myDiv
 *   toggleElement(myDiv, false); // shows myDiv
 */
export function toggleElement(element, hide = true) {

    if (!element || element === undefined || element === null) {
        console.log("there is no elemnent")
        return;
    }

    if (hide) {
        element.classList.add("d-none");
        return
    }

    element.classList.remove("d-none");
}



/**
 * A no-operation (doNothing) function.
 * 
 * This function does nothing and returns undefined.
 * It can be used as a placeholder callback or a safe default
 * to explicitly indicate that no action should be taken.
 *
 * @example
 * try {
 *   toggleElement(testSetupFormElement);
 * } catch (error) {
 *   noop(); // ignore errors
 * }
 *
 * @example
 * button.addEventListener("click", noop); // no action on click
 */
export const doNothing = () => {};



/**
 * Clears all child content of a given DOM element.
 *
 * @param {HTMLElement} element - The element to clear.
 *
 * Notes:
 * - Uses a helper function `checkIfHTMLElement` to validate the element before clearing.
 * - Sets `innerHTML` to an empty string, effectively removing all child nodes.
 *
 * Example usage:
 *   const container = document.getElementById("container");
 *   clearElement(container); // removes all children from container
 */
export function clearElement(element) {
    if (!checkIfHTMLElement(element, element.tagName)) {
        return;
    }

    element.innerHTML = "";
}


/**
 * Fetches a DOM element by ID and caches it in a variable.
 *
 * @param {HTMLElement|null} cachedElement - The current cached reference (may be null/undefined).
 * @param {string} elementId - The ID of the DOM element to fetch.
 * @returns {HTMLElement|null} The cached element or the newly fetched one.
 */
export function getOrFetchElement(cachedElement, elementId) {
    if (!cachedElement) {
        cachedElement = document.getElementById(elementId);
    }
    return cachedElement;
}

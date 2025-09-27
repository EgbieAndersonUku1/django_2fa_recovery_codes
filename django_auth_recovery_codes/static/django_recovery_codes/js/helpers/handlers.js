import appStateManager from "../state/appStateManager.js";
import { applyDashToInput, sanitizeText } from "../utils.js";

/**
 * A Helper function that processes input events for a text field by validating its length,
 * sanitising its content, converting it to uppercase, and formatting it with dashes.
 *
 * This function is intended to be called within other event handlers
 * to keep input field logic modular and reusable.
 * 
 * The handle helper functions ensure that only the allowed values (A-Z, 2-9) 
 * are rendered in the form. 
 * 0 and 1 are not allowed because they can easily be confused with the letters 
 * O and I.
 * 
 * @param {Event} e - The input event triggered by the text field.
 * @returns {void}
 */
export function handleInputFieldHelper(e) {

    const inputField = e.target;

    if (!e || !e.target) {
        return;
    }

    if (inputField && inputField.validity.tooShort) {
        const charsNeeded = inputField.minLength - inputField.value.length;
        inputField.setCustomValidity(
            `Minimum length is ${inputField.minLength}. Please enter ${charsNeeded > 0 ? charsNeeded : 0} more character(s).`
        );
    } else {
        inputField.setCustomValidity(''); // reset
    }

    const LENGTH_PER_DASH = appStateManager.getLengthPerDashInputField();

    e.target.value = sanitizeText(inputField.value, false, true, ["2", "3", "4", "5", "6", "7", "8", "9"]);
    applyDashToInput(e, LENGTH_PER_DASH);


}




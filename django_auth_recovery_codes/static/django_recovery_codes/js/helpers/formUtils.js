import { checkIfHTMLElement } from "../utils.js";
import { parseFormData } from "../form.js";


/**
 * Helper function that handles generic form submissions by validating the form
 * and extracting its data in a structured format.
 *
 *
 * This function is designed for reuse across multiple form submission scenarios
 * to centralise validation and data parsing logic.
 *
 * @param {Event} e - The submit event triggered by the form.
 * @param {HTMLFormElement} formElement - The form element being submitted.
 * @param {string[]} requiredFields - An array of field names that must be present in the form data.
 * @returns {Object|undefined} An object containing parsed form data if validation succeeds;
 *                              otherwise, undefined if validation fails.
 */
export function handleFormSubmissionHelper(e, formElement, requiredFields) {

    if (!e || !e.target) {
        return;
    }

    checkIfHTMLElement(formElement, "Form Element");

    if (!Array.isArray(requiredFields)) {
        logError("handleFormSubmissionHelper", `The form required list must be an array. Expected an array but got type ${type(requiredFields)}`);
        return;
    }

    e.preventDefault();


    if (!formElement.checkValidity()) {
        formElement.reportValidity();
        return
    }

    const formData = new FormData(formElement);
    return parseFormData(formData, requiredFields);
}



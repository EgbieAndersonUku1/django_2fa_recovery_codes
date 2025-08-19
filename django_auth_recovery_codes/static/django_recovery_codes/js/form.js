/**
 * Parses FormData and extracts required fields, converting keys to camelCase.
 * 
 * @param {FormData} formData - The FormData object to be parsed.
 * @param {string[]} requiredFields - An array of field names that must be present in the FormData.
 * 
 * @returns {Object} An object containing the parsed data with keys converted to camelCase.
 * 
 * @throws {Error} If:
 *   - formData is not an instance of FormData.
 *   - requiredFields is not a non-empty array.
 *   - A required field is missing or its value is empty.
 * 
 * @example
 * const formData = new FormData();
 * formData.append("first_name", "Alice");
 * formData.append("email", "alice@example.com");
 * formData.append("mobile", "1234567890");
 * 
 * const requiredFields = ["first_name", "email", "mobile"];
 * const parsedData = parseFormData(formData, requiredFields);
 * console.log(parsedData); 
 * // Output: { firstName: "Alice", email: "alice@example.com", mobile: "1234567890" }
 */
export function parseFormData(formData, requiredFields = []) {

    if (!(formData instanceof FormData)) {
        throw new Error(`Expected a FormData object but got type ${typeof formData}`);
    }

    if (!Array.isArray(requiredFields)) {
        throw new Error(`The requiredFields argument must be an array, but got type: ${typeof requiredFields}`);
    }

    if (requiredFields.length === 0) {
        throw new Error(`The required Fields array is empty. Please provide at least one field name.`);
    }

    const result = {};

    for (const field of requiredFields) {
        const value = formData.get(field);
        
        if (!value) { 
            throw new Error(`Missing or empty required 'name' field: ${field}`);
        }
        
        const camelCaseField = field.toLowerCase().replace(/[-_](.)/g, (_, char) => char.toUpperCase());
        result[camelCaseField] = value;
    }

    return result;
}

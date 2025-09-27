/**
 * Retrieves the CSRF token from the HTML document.
 *
 * @throws {Error} Throws if the CSRF token element is not found.
 * @returns {string} The content of the CSRF token.
 */
export function getCsrfToken() {
    const csrfToken = document.getElementById("csrf_token");

    if (csrfToken === null) {
        throw new Error("The CSRF token return null, CSRF Token is needed for security of the application")
      
    }

    return csrfToken.content
}


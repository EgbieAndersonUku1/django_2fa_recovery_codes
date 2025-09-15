export function getCsrfToken() {
    const csrfToken = document.getElementById("csrf_token");

    if (csrfToken === null) {
        throw new Error("The CSRF token return null, CSRF Token is needed for security of the application")
      
    }

    return csrfToken.content
}


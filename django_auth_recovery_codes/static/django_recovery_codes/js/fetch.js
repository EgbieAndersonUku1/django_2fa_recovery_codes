/**
 * Asynchronously sends an HTTP request to the specified URL and returns the parsed JSON response.
 * 
 * Supports only "POST" and "GET" methods. For POST requests, the body must be a non-null object.
 * Optionally includes a CSRF token header if provided.
 * 
 * @param {Object}   params
 * @param {string}   params.url         - The endpoint URL to send the request to.
 * @param {?string}  [params.csrfToken] - Optional CSRF token to include in the request headers.
 * @param {?Object}  [params.body]      - Request payload for POST method. Must be an object.
 * @param {string}   [params.method="POST"] - HTTP method to use ("POST" or "GET").
 * 
 * @throws {Error} Throws if an invalid method is used, or if POST body is invalid, 
 *                 or if the server response is not ok.
 * 
 * @returns {Promise<Object>} Resolves with the parsed JSON data from the server response.
 */
export default async function fetchData({ url, csrfToken = null, body = null, method = "POST" }) {

    try {

        const allowedMethods = ["POST", "GET"];

        
        if (!allowedMethods.includes(method)) {
            throw new Error(`Invalid method: ${method}. Allowed methods are ${allowedMethods.join(", ")}`);
        };

     
        if (method === "POST" && (typeof body !== "object")) {
               throw new Error(`Body must be a non-null object for POST requests, received: ${typeof body}`);
        }


        const headers = {
            "Content-Type": "application/json",
        };

        if (csrfToken) {
            headers["X-CSRFToken"] = csrfToken;
        };

        const options = {
            method,
            headers,
        };

    
         if (method === "POST" && body) {
            options.body = JSON.stringify(body);
        };

        const response = await fetch(url, options);
        const data     = await response.json();

        if (!response.ok) {
            console.log(`HTTP error! Status: ${response.status}`);
            throw new Error(`${data.ERROR || "Unknown Error"}`);
        }

        return data;

    } catch (error) {

        console.error("Fetch error:", error);
        throw new Error(`${error}`);
      
    }
}


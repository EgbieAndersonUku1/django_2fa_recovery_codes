/**
 * Asynchronously sends an HTTP request to the specified URL and returns the parsed JSON response.
 * 
 * Supports only "POST" and "GET" methods. For POST requests, the body must be a non-null object.
 * Optionally includes a CSRF token header if provided.
 * 
 * 
 * Automatically logs useful debugging information if a request fails, including:
 * - URL
 * - HTTP status code
 * - Status text
 * - Response headers
 * - Parsed JSON body (if available)
 * 
 * 
 * @param {Object}   params
 * @param {string}   params.url                   - The endpoint URL to send the request to.
 * @param {?string}  [params.csrfToken]          - Optional CSRF token to include in the request headers.
 * @param {?Object}  [params.body]               - Request payload for POST method. Must be an object.
 * @param {string}   [params.method="POST"]      - HTTP method to use ("POST" or "GET").
 * @param {boolean}  [params.returnRawResponse=false] - If true, returns the raw fetch Response object 
 *                                                      instead of parsing JSON (useful for file downloads).
 * @param {boolean}  [params.throwOnError=true]  - If true, throws an error for non-ok responses.
 *                                                  If false, returns the Response and the data object even for errors.
 * 
 * @throws {Error} Throws if an invalid method is used, POST body is invalid, or response is not ok
 *                 (and throwOnError is true).
 * 
 * @returns {Promise<Object|Response>} Resolves with parsed JSON data, or raw Response if returnRawResponse
 *                                    is true, or Response on error if throwOnError is false.
 * 
 * /**
 * @example
 * // Normal API call (throws on error)
 * try {
 *   const data = await fetchData({
 *       url: "/api/get-user/",
 *       method: "POST",
 *       body: { userId: 123 }
 *   });
 *   console.log(data);
 * } catch (err) {
 *   console.error("Error fetching user:", err.message);
 * }
 * 
 * @example
 * // API call returning response on error (does not throw)
 * const { response, data } = await fetchData({
 *   url: "/api/login/",
 *   method: "POST",
 *   body: { username: "test", password: "wrong" },
 *   throwOnError: false
 * });
 * 
 * if (!response.ok) {
 *   console.log("Login failed:");
 *   console.log("Status:", response.status);
 *   console.log("Response body:", data);
 * } else {
 *   console.log("Login successful:", data);
 * }
 * 
 * @example
 * 
 * // File download
 * const response = await fetchData({
 *   url: "/download/report.pdf",
 *   method: "GET",
 *   returnRawResponse: true
 * });
 * 
 * const blob = await response.blob();
 * const filename = response.headers.get("Content-Disposition")
 *     ?.split("filename=")[1].replace(/['"]/g, "") || "file.pdf";
 * const a = document.createElement("a");
 * a.href = URL.createObjectURL(blob);
 * a.download = filename;
 * a.click();
 */
export default async function fetchData({ url, 
                                      csrfToken = null, 
                                      body = null, 
                                      method = "POST", 
                                      returnRawResponse = false,
                                      throwOnError = true,
                                    }) {

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

        if (returnRawResponse) {
            return response;
        }

        const data = await response.json();

        if (!response.ok) {
             
            // Log useful information for debugging
            if (throwOnError) {

                console.error("Fetch error details:");
                console.error("URL:", response.url);
                console.error("Status:", response.status);
                console.error("Status Text:", response.statusText);
                console.error("Headers:", response.headers);
                console.error("Body:", data);

                throw new Error(`${data || "Unknown Error"}`);
            }

            // Return structured object if throwOnError is false
            return {response: response, data: data}
           
        }

        return data;

    } catch (error) {

        console.error("Fetch error:", error.message);
        throw new Error(`${error}`);
      
    }
}


/**
 * Logs errors to the console with a consistent format.
 * @param {string} functionName - The name of the function where the error occurred.
 * @param {Error} error - The error object to log.
 */
export function logError(functionName, error)  {
    consoleLogrHelper(functionName, error);
}


/**
 * Warn errors to the console with a consistent format.
 * @param {string} functionName - The name of the function where the error occurred.
 * @param {Error} error - The error object to log.
 */
export function warnError(functionName, error)  {
    consoleLogrHelper(functionName, error, true);
}


function consoleLogrHelper(functionName, error, warn=false) {
    const timestamp = new Date().toISOString();   
    const logger = warn ? console.warn : console.error;
    logger(`[${timestamp}] [${functionName}] Error:`, error);


}
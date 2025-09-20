import { handleInputFieldHelper } from "../helpers/handlers.js";
import { checkIfFormHTMLElement, checkIfInputHTMLElement, toggleSpinner, showSpinnerFor } from "../utils.js";


const loginForm       = document.getElementById("login-recovery-form");
const loginInputField = document.getElementById("recovery-code-input");
const spinner         = document.getElementById("login-recovery-loader");


loginInputField.addEventListener("input", handleInputFieldHelper);


loginForm.addEventListener("submit", handleLoginFormSubmission);



function handleLoginFormSubmission(e) {
    e.preventDefault();
    const MILLI_SECONDS = 2000;

    showSpinnerFor(spinner, MILLI_SECONDS);

    setTimeout(() => {
        loginForm.submit();
    }, MILLI_SECONDS);

    
}




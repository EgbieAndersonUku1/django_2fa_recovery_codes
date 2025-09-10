import { toggleSpinner } from "./utils.js";

const resultContainer = document.getElementById("dynamic-verify-form-container");


const MILLI_SECONDS = 1000;

export function clearTestResultContainer() {
    resultContainer.innerHTML = "";
}

export async function displayResults(results) {
    const divTestResultContainer     = document.createElement("div");
    const MILLI_SECONDS              = 1000;
    divTestResultContainer.id        = "test-result"
    divTestResultContainer.className = "padding-top-md";

    divTestResultContainer.classList.add("margin-top-lg");
    
    const titleElement = createTitle();
    resultContainer.appendChild(titleElement);

    const keys = Object.keys(results).filter(key => key !== "SUCCESS");

    console.log(results)
    keys.forEach((key, index) => {

        setTimeout(() => {
            const message = results[key];

            if (key !== "FAILURE") {
                if (message) {

             
                const divResult = createResultDiv(message);

                divResult.classList.remove("text-red", "text-green")
              
                results.FAILURE ? divResult.classList.add("text-red") : divResult.classList.add("text-green")
              
            
                resultContainer.appendChild(divResult);
                }
            }
            
          
        }, index * MILLI_SECONDS); 

     return true 
    });
}


function createTitle(title = "Test setup result",  className = "bold") {
    return createResultDiv(title, className);
}


function createResultDiv(message, className = null) {

    const divContainer = document.createElement("div");
    const divSpinner   = document.createElement("div");
    const divResult    = document.createElement("div");
    const spanElement  = document.createElement("span");
    const pElement     = document.createElement("p");

    divContainer.classList.add("result-div", "two-column-grid--5-95");
    divSpinner.classList.add("spinner");


    spanElement.classList.add("loader", "bg-green", "test-loader");
    divResult.classList.add("result-title");

    const icon     = document.createElement("i");
    icon.className = "fa-brands fa-hashnode";

    pElement.appendChild(icon);
    pElement.appendChild(document.createTextNode(` ${message}`));

    if (className !== null) {
        pElement.className = className;
    }

    toggleSpinner(spanElement)

    divSpinner.appendChild(spanElement);
    divContainer.appendChild(divSpinner);
   
    setTimeout(() => {

        divContainer.appendChild(divResult);
      
    }, MILLI_SECONDS * 2)

     setTimeout(() => {
        divResult.appendChild(pElement);
        toggleSpinner(spanElement, false)
    }, MILLI_SECONDS * 3)
   
  
    return divContainer

}

